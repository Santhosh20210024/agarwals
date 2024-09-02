import frappe
from agarwals.agarwals.doctype import file_records
from agarwals.reconciliation.step.cancellator.cancellator import PaymentDocumentCancellator
from agarwals.reconciliation.step.cancellator.utils.matcher_cancellator import MatcherCancellator
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
                PaymentDocumentCancellator().cancel_payment_documents(bill)
                MatcherCancellator().delete_matcher(sales_invoice_record)  
                sales_invoice_record.reload()
                sales_invoice_record.cancel()
                
                frappe.db.set_value('Bill', bill, {'invoice_status': 'CANCELLED'})
                
                frappe.db.commit()
                file_records.create(file_upload=sales_invoice_record.custom_file_upload,
                                    transform=sales_invoice_record.custom_transform,
                                    reference_doc=sales_invoice_record.doctype,
                                    record=bill, index=sales_invoice_record.custom_index)
            except Exception as e:
                log_error(error=e, doc="Bill",doc_name=bill)
             
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
                                            'custom_patient_name': bill_record.patient_name,
                                            'custom_ma_claim_id': bill_record.ma_claim_id,
                                            'custom_claim_id': bill_record.claim_id, 'customer': bill_record.customer,
                                            'entity': bill_record.entity, 'region': bill_record.region,
                                            'branch': bill_record.branch, 'branch_type': bill_record.branch_type,
                                            'cost_center': bill_record.cost_center,
                                            'custom_patient_age' : bill_record.patient_age,
                                            'items': [
                                                {'item_code': 'Claim', 'rate': bill_record.claim_amount, 'qty': 1}],
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
                    frappe.db.set_value('Bill', bill_number,
                                        {'invoice': sales_invoice_record.name, 'invoice_status': bill_record.status})
                    frappe.db.commit()
                    if sales_invoice_record.status != 'Cancelled':
                        update_fiscal_year(sales_invoice_record, 'Sales Invoice')

                    file_records.create(file_upload=sales_invoice_record.custom_file_upload,
                                        transform=sales_invoice_record.custom_transform,
                                        reference_doc=sales_invoice_record.doctype,
                                        record=bill_number, index=sales_invoice_record.custom_index)
                except Exception as e:
                    log_error(error= 'Unable to Create Sales Invoice: ' + str(e), doc="Bill", doc_name=bill_number)
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")

    def enqueue_jobs(self, bill_number, args):
        no_of_invoice_per_queue = int(args["chunk_size"])
        for i in range(0, len(bill_number), no_of_invoice_per_queue):
            chunk_doc = chunk.create_chunk(args["step_id"])
            frappe.enqueue(self.process, queue=args["queue"], is_async=True, timeout=18000,
                           bill_numbers=bill_number[i:i + no_of_invoice_per_queue], chunk_doc=chunk_doc)
    def skip_invoice_process(self,skip_bills):
        for skip_bill in skip_bills:
            frappe.db.set_value('Bill',skip_bill,'status','CANCELLED AND DELETED')
        frappe.db.commit()
        
    def find_skip_bills(self):
        customer_list = frappe.get_all('Customer',filters = {'custom_skip_invoice_process':1},pluck = 'name')
        if not customer_list:
            return []
        return frappe.get_all('Bill',filters={'customer':['in', customer_list],'status':'RAISED' },pluck='name')        

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
            
        skip_bills = SalesInvoiceCreator().find_skip_bills()   
        if skip_bills:
            SalesInvoiceCreator().skip_invoice_process(skip_bills)
        
        new_bills = frappe.get_list('Bill', filters={'invoice': '', 'status': ['!=', 'CANCELLED AND DELETED']},
                                    pluck='name')
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