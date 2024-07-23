import frappe
from agarwals.agarwals.doctype import file_records
from agarwals.utils.payment_entry_cancellator import PaymentEntryCancellator
from agarwals.utils.journal_entry_cancellator import JournalEntryCancellator
from agarwals.utils.Matcher_Reference_Cancellator import MatcherReferenceCancellator
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from agarwals.utils.fiscal_year_update import update_fiscal_year

class SalesInvoiceCreator:
    def cancel_sales_invoice(self, cancelled_bills):
        for bill in cancelled_bills:
            try:
                bill_record = frappe.get_doc('Bill', bill)
                sales_invoice_record = frappe.get_doc('Sales Invoice', bill)
                sales_invoice_record.custom_file_upload = bill_record.file_upload
                sales_invoice_record.custom_transform = bill_record.transform
                sales_invoice_record.custom_index = bill_record.index
                sales_invoice_record.save(ignore_permissions=True)
                journal_entry_doc = frappe.get_all('Journal Entry Account', filters={'reference_name': bill, 'reference_type':'Sales Invoice'}, pluck = 'parent')
                sales_invoice_record.cancel()
                PaymentEntryCancellator().cancel_payment_entry(bill)
                if journal_entry_doc:
                    JournalEntryCancellator().cancel_journal_entry(journal_entry_doc)
                MatcherReferenceCancellator().delete_matcher_reference(bill)
                frappe.db.set_value('Bill', bill, {'invoice_status': 'CANCELLED'})
                self.delete_sales_invoice_reference(bill)
                frappe.db.commit()
                file_records.create(file_upload=sales_invoice_record.custom_file_upload,
                                    transform=sales_invoice_record.custom_transform, reference_doc=sales_invoice_record.doctype,
                                    record=bill, index=sales_invoice_record.custom_index)
            except Exception as e:
                log_error(error=e, doc="Bill",doc_name=bill)
                # error_log = frappe.new_doc('Error Record Log')
                # error_log.set('doctype_name', 'Bill')
                # error_log.set('reference_name', bill)
                # error_log.set('error_message', e)
                # error_log.save()

    def delete_sales_invoice_reference(self, bill):
        frappe.db.sql(f"DELETE FROM `tabSales Invoice Reference` WHERE parent = '{bill}'")
        

    def process(self, bill_numbers, chunk_doc):
        chunk.update_status(chunk_doc, "InProgress")
        try:
            for bill_number in bill_numbers:
                try:
                    bill_record = frappe.get_doc('Bill', bill_number)
                    bill_record.set("region", frappe.get_doc('Branch', bill_record.branch).custom_region)
                    bill_record.set("customer", frappe.get_doc('Payer Alias', bill_record.payer).payer_final_name)
                    bill_record.set("branch_type", frappe.get_doc('Branch', bill_record.branch).custom_branch_type)
                    bill_record.save()
                    sales_invoice_record = frappe.new_doc('Sales Invoice')
                    sales_invoice_params = {'custom_bill_no': bill_record.bill_no, 'custom_mrn': bill_record.mrn,
                                            'custom_patient_name': bill_record.patient_name, 'custom_ma_claim_id': bill_record.ma_claim_id,
                                            'custom_claim_id': bill_record.claim_id, 'customer': bill_record.customer,
                                            'entity': bill_record.entity, 'region': bill_record.region,
                                            'branch': bill_record.branch, 'branch_type': bill_record.branch_type,
                                            'cost_center': bill_record.cost_center,
                                            'items': [{'item_code': 'Claim', 'rate': bill_record.claim_amount, 'qty': 1}],
                                            'set_posting_time': 1, 'posting_date': bill_record.bill_date,
                                            'due_date': bill_record.bill_date,
                                            'custom_file_upload': bill_record.file_upload,
                                            'custom_transform': bill_record.transform,
                                            'custom_index': bill_record.index}
                    for key, value in sales_invoice_params.items():
                        sales_invoice_record.set(key, value)
                    sales_invoice_record.save()
                    sales_invoice_record.submit()
                    if bill_record.status == 'CANCELLED':
                        sales_invoice_record.cancel()
                    frappe.db.set_value('Bill', bill_number, {'invoice': sales_invoice_record.name, 'invoice_status': bill_record.status})
                    frappe.db.commit()
                    if sales_invoice_record.status != 'Cancelled':
                       update_fiscal_year(sales_invoice_record,'Sales Invoice')
                    
                    file_records.create(file_upload=sales_invoice_record.custom_file_upload,
                                        transform=sales_invoice_record.custom_transform, reference_doc=sales_invoice_record.doctype,
                                        record=bill_number, index=sales_invoice_record.custom_index)
                except Exception as e:
                    log_error(error=str(e), doc="Bill", doc_name=bill_number)
                    # error_log = frappe.new_doc('Error Record Log')
                    # error_log.set('doctype_name', 'Bill')
                    # error_log.set('reference_name', bill_number)
                    # error_log.set('error_message', 'Unable to Create Sales Invoice: ' + str(e))
                    # error_log.save()
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")

    def enqueue_jobs(self, bill_number, args):
        no_of_invoice_per_queue = int(args["chunk_size"])
        for i in range(0, len(bill_number), no_of_invoice_per_queue):
            chunk_doc = chunk.create_chunk(args["step_id"])
            frappe.enqueue(self.process, queue=args["queue"], is_async=True, timeout=18000,
                           bill_numbers=bill_number[i:i + no_of_invoice_per_queue],chunk_doc=chunk_doc)

@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        cancelled_bills = frappe.get_list('Bill', filters={'status': 'CANCELLED', 'invoice_status': 'RAISED'},
                                          pluck='name')
        cancellation_chunk_doc = chunk.create_chunk(args["step_id"])
        if cancelled_bills:
            chunk.update_status(cancellation_chunk_doc, "InProgress")
            try:
                SalesInvoiceCreator().cancel_sales_invoice(cancelled_bills)
                cancellation_chunk_doc_status = "Processed"
            except Exception as e:
                cancellation_chunk_doc_status = "Error"
        else:
            cancellation_chunk_doc_status = "Processed"
        new_bills = frappe.get_list('Bill', filters={'invoice': '', 'status': ['!=','CANCELLED AND DELETED']},pluck = 'name')
        if new_bills:
            SalesInvoiceCreator().enqueue_jobs(new_bills, args)
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
        chunk.update_status(cancellation_chunk_doc, cancellation_chunk_doc_status)
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e, 'Step')