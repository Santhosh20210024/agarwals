import frappe
from agarwals.agarwals.doctype import file_records
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error

class JournalUtils():
    def create_journal_entry(self, type, date):
        je = frappe.new_doc('Journal Entry')
        je.voucher_type = type
        je.posting_date = date
        return je

    def fetch_invoice_details(self, invoice):
        return frappe.get_doc('Sales Invoice', invoice)

    def add_account_entries(self, je, invoice, from_account, to_account, amount):
        je.append('accounts', {
                'account': from_account,
                'party_type': 'Customer',
                'party': invoice.customer,
                'credit_in_account_currency': amount,
                'reference_type': 'Sales Invoice',
                'reference_name': invoice.name,
                'reference_due_date': invoice.posting_date,
                'region': invoice.region,
                'entity': invoice.entity,
                'branch': invoice.branch,
                'cost_center': invoice.cost_center,
                'branch_type': invoice.branch_type
                })
        je.append('accounts', {
        'account': to_account,
        'party_type': 'Customer',
        'party': invoice.customer,
        'debit_in_account_currency': amount,
        'user_remark': to_account,
        'region': invoice.region,
        'entity': invoice.entity,
        'branch': invoice.branch,
        'cost_center': invoice.cost_center,
        'branch_type': invoice.branch_type
        })
        return je

    def save_je(self, je, parent_doc = None):
        if parent_doc:
            je.custom_file_upload = parent_doc.transform
            je.custom_transform = parent_doc.transform
            je.custom_index = parent_doc.index
        je.save()
        je.submit()
        frappe.db.commit()
        if parent_doc:
            file_records.create(file_upload=je.custom_file_upload, transform=je.custom_transform, reference_doc=je.doctype,
                                record=je.name, index=je.custom_index)

class BillAdjustmentProcess(JournalUtils):
    def __init__(self):
       super().__init__()

    # Unit-Tested
    def update_invoice_reference(self,
                                 sales_invoice,
                                 date,
                                 je_name,
                                 tds_amount = 0,
                                 disallowance_amount = 0):

        sales_doc = self.fetch_invoice_details(sales_invoice)
        allocated_amount = tds_amount if tds_amount else disallowance_amount
        sales_doc.append('custom_reference', {'entry_type': 'Journal Entry'
                                              ,'entry_name': je_name
                                              ,'tds_amount': tds_amount
                                              ,'disallowance_amount': disallowance_amount
                                              ,'allocated_amount': allocated_amount
                                              ,'utr_date': date })
        sales_doc.save()
        frappe.db.commit()

    def process_bill_adjust(self, bill_list, chunk_doc):
        chunk.update_status(chunk_doc,"InProgress")
        try:
            for bill_adjt in bill_list:
                invoice = self.fetch_invoice_details(bill_adjt.bill)
                valid_tds = False
                valid_dis = False
                try:
                    if bill_adjt.tds:
                        je = self.create_journal_entry('Credit Note', bill_adjt.posting_date)
                        je.name = "".join([bill_adjt.bill,'-','TDS'])
                        je = self.add_account_entries(je, invoice, 'Debtors - A', 'TDS - A', bill_adjt.tds)
                        self.save_je(je, bill_adjt)
                        self.update_invoice_reference(bill_adjt.bill, bill_adjt.posting_date, je.name,
                                                      tds_amount=bill_adjt.tds)
                        valid_tds = True
                except Exception as e:
                    error_log = frappe.new_doc('Error Record Log')
                    error_log.set('doctype_name', 'Bill Adjustment')
                    error_log.set('reference_name', bill_adjt.bill)
                    error_log.set('error_message', '' + str(e))
                    bill_adjt.error_remark = str(e)
                    error_log.save()
                try:
                    if bill_adjt.disallowance:
                        je = self.create_journal_entry('Credit Note', bill_adjt.posting_date)
                        je.name = "".join([bill_adjt.bill,'-','DIS'])
                        je = self.add_account_entries(je, invoice, 'Debtors - A', 'Disallowance - A', bill_adjt.disallowance)
                        self.save_je(je, bill_adjt)
                        self.update_invoice_reference(bill_adjt.bill, bill_adjt.posting_date, je.name,
                                                      disallowance_amount=bill_adjt.disallowance)
                        valid_dis = True
                except Exception as e:
                    error_log = frappe.new_doc('Error Record Log')
                    error_log.set('doctype_name', 'Bill Adjustment')
                    error_log.set('reference_name', bill_adjt.bill)
                    error_log.set('error_message', '' + str(e))
                    bill_adjt.error_remark = str(e)
                    error_log.save()
                # Need to refactor this part
                if bill_adjt.tds and bill_adjt.disallowance:
                    if valid_dis and valid_tds:
                            doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                            doc.status = 'Processed'
                            doc.save()
                    elif valid_tds or valid_dis:
                            doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                            doc.status = 'Partially Processed'
                            doc.save()
                    else:
                        doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                        doc.status = 'Error'
                        doc.save()
                if bill_adjt.tds:
                    if valid_tds:
                        doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                        doc.status = 'Processed'
                        doc.save()
                    else:
                        doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                        doc.status = 'Error'
                        doc.save()
                if bill_adjt.disallowance:
                    if valid_dis:
                        doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                        doc.status = 'Processed'
                        doc.save()
                    else:
                        doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                        doc.status = 'Error'
                        doc.save()
            chunk.update_status(chunk_doc,"Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")

@frappe.whitelist()
def process(args):
    try:
        args=cast_to_dic(args)
        n = int(args["chunk_size"])
        batch_number=0
        bills = frappe.get_list('Bill Adjustment', fields = ['bill','tds','disallowance','posting_date'], filters = {'status': 'Open'})
        if bills:
            for _index in range(0, len(bills), n):
                chunk_doc=chunk.create_chunk(args["step_id"])
                batch_number = batch_number + 1
                frappe.enqueue(BillAdjustmentProcess().process_bill_adjust, queue=args["queue"], is_async=True, job_name="BillAdjustmentBatch" + str(batch_number), timeout=25000,
                            bill_list = bills[_index:_index + n],chunk_doc=chunk_doc)
        else:
                chunk_doc = chunk.create_chunk(args["step_id"])
                chunk.update_status(chunk_doc, "Processed")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')