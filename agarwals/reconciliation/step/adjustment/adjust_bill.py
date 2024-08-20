import frappe
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from agarwals.reconciliation.step.adjustment.journal_entry_utils import (
    JournalEntryUtils
)


class BillAdjustmentProcessor(JournalEntryUtils):
    """BillAdjustmentProcessor is the class used to perform journal entry process from the bill adjustment entries"""
    
    def __init__(self):
        super().__init__('Sales Invoice')
        self.TDS_ACCOUNT = "TDS - A"
        self.DISALLOWANCE_ACCOUNT = "Disallowance - A"
        self.DEBTORS_ACCOUNT = "Debtors - A"
        self.error_message = ""
        self.error_items = []

    def _add_custom_fields(self, je, invoice):
        je.custom_entity = invoice.entity
        je.custom_branch = invoice.branch
        je.custom_region = invoice.region
        je.custom_branch_type = invoice.branch_type
        je.custom_bill_date = invoice.posting_date
        je.custom_party_group = invoice.customer_group
        je.custom_party = invoice.customer
        return je

    def process_entry(
        self, bill_adjt, invoice, entry_type, account_debit, account_credit, amount
    ):
        try:
            if str(amount).strip():
                je = self.create_journal_entry("Credit Note", bill_adjt.posting_date)
                je = self.set_je_name(invoice.name, "-", entry_type,je=je)
                je = self.add_account_entries(
                    je, invoice, account_debit, account_credit, amount
                )
                self.save_je(je, bill_adjt)
                return je.name
        except Exception as e:
            self.error_message += f"Error while processing {entry_type} entry: {e}\n"
            self.error_items.append(entry_type)
            return None
    
    def check_invoice(self, sales_doc):
        """Method to handle the invoice status"""
        if sales_doc.status in ['Paid', 'Cancelled']:
            return False
        return True

    def process_bill_adjust(self, bill_adjustment_list, chunk_doc):
        chunk.update_status(chunk_doc, "InProgress")
        
        try:
            for bill_adjt in bill_adjustment_list:
                bill_adjt = frappe.get_doc('Bill Adjustment', bill_adjt)
                invoice = self.fetch_doc_details('Sales Invoice', bill_adjt.bill)
	            
                if self.check_invoice(invoice):
                    if bill_adjt.tds >= 1:
                        bill_adjt.tds_entry_id = self.process_entry(
	                        bill_adjt,
	                        invoice,
	                        "TDS",
	                        self.DEBTORS_ACCOUNT,
	                        self.TDS_ACCOUNT,
	                        bill_adjt.tds,
	                    )
                      
                    if bill_adjt.disallowance >= 1:
                        bill_adjt.dis_entry_id = self.process_entry(
	                        bill_adjt,
	                        invoice,
	                        "DIS",
	                        self.DEBTORS_ACCOUNT,
	                        self.DISALLOWANCE_ACCOUNT,
	                        bill_adjt.disallowance,
	                    )

                    if not self.error_items:
                        bill_adjt.status = "Processed"
                    elif len(self.error_items) == 1:
                        bill_adjt.status = "Partially Processed"
                    else:
                        bill_adjt.status = "Error"

                    if self.error_message:
                        bill_adjt.error_remark = self.error_message
                        log_error(bill_adjt.error_remark, doc='Bill Adjustment', doc_name=bill_adjt.name)
                else:
                    bill_adjt.status = 'Error'
                    bill_adjt.error_remark = f'{invoice.status} Bill'
                    log_error(bill_adjt.error_remark, doc='Bill Adjustment', doc_name=bill_adjt.name)
	        
                bill_adjt.save()
                frappe.db.commit()
            chunk.update_status(chunk_doc, "Processed")
        except Exception as _:
            chunk.update_status(chunk_doc, "Error")


class BillAdjustmentOrchestrator:
    """BillAdjustmentOrchestrator used for orchestrating the chunk creation and enqueueing the appropriate process"""
    
    def get_bill_adjustments(self):
        return frappe.get_list(
            "Bill Adjustment",
            filters={"status": "Open"},
            pluck='name'
        )

    def start_process(self, args):
        args = cast_to_dic(args)
        chunk_size = int(args.get("chunk_size", 100))
        batch_no = 0

        bill_adjustments = self.get_bill_adjustments()
        if not bill_adjustments:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
            return

        for bill_adjt_chunk in self._chunk_list(bill_adjustments, chunk_size):
            chunk_doc = chunk.create_chunk(args["step_id"])
            batch_no = batch_no + 1
            self._enqueue_bill_adjustment(args, bill_adjt_chunk, chunk_doc, batch_no)

    def _chunk_list(self, iterable, n):
        """Yield successive n-sized chunks from the iterable."""
        for i in range(0, len(iterable), n):
            yield iterable[i : i + n]

    def _enqueue_bill_adjustment(self, args, bill_adjt_chunk, chunk_doc, batch_no):
        try:
            frappe.enqueue(
                BillAdjustmentProcessor().process_bill_adjust,
                queue=args.get("queue", "long"),
                is_async=True,
                job_name=f"BillAdjustment_Batch{batch_no}",
                timeout=25000,
                bill_adjustment_list=bill_adjt_chunk,
                chunk_doc=chunk_doc,
            )
        except Exception as e:
            self._handle_error(e, args["step_id"])

    def _handle_error(self, error, step_id):
        chunk_doc = chunk.create_chunk(step_id)
        chunk.update_status(chunk_doc, "Error")
        log_error(error, "Step")

@frappe.whitelist()
def process(args):
    BillAdjustmentOrchestrator().start_process(args)