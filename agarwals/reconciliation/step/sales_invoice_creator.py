import frappe
from agarwals.agarwals.doctype import file_records
from agarwals.reconciliation.step.cancellator.cancellator import PaymentDocumentCancellator
from agarwals.reconciliation.step.cancellator.utils.matcher_cancellator import MatcherCancellator
from tfs.orchestration import ChunkOrchestrator
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from agarwals.utils.fiscal_year_update import update_fiscal_year


class SalesInvoiceCreator:
    @ChunkOrchestrator.update_chunk_status
    def cancel_sales_invoice(self, cancelled_bills):
        status = "Processed"
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
                status = "Error"
                log_error(error=e, doc="Bill",doc_name=bill)
        return status

    @ChunkOrchestrator.update_chunk_status
    def process(self, bill_numbers):
        status = "Processed"
        for bill_number in bill_numbers:
            try:
                bill_record = frappe.get_doc('Bill', bill_number)
                bill_record.set("region", frappe.get_doc('Branch', bill_record.branch).custom_region)
                bill_record.set("customer", frappe.get_doc('Payer Alias', bill_record.payer).payer_final_name)
                bill_record.set("branch_type", frappe.get_doc('Branch', bill_record.branch).custom_branch_type)
                bill_record.save()
                skip_invoice_customer_list = self.get_skip_invoice_customer()
                if bill_record.customer in skip_invoice_customer_list:
                    bill_record.set("status","CANCELLED AND DELETED")
                    bill_record.save()
                    frappe.db.commit()
                    continue
                sales_invoice_record = frappe.new_doc('Sales Invoice')
                sales_invoice_params = {'custom_bill_no': bill_record.bill_no, 'custom_mrn': bill_record.mrn,
                                        'custom_patient_name': bill_record.patient_name,
                                        'custom_ma_claim_id': bill_record.ma_claim_id,
                                        'custom_claim_id': bill_record.claim_id, 'customer': bill_record.customer,
                                        'entity': bill_record.entity, 'region': bill_record.region,
                                        'branch': bill_record.branch, 'branch_type': bill_record.branch_type,
                                        'cost_center': bill_record.cost_center,
                                        'custom_patient_age' : bill_record.patient_age,
                                        'custom_payer_name' : bill_record.payer,
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
                status = "Error"
                log_error(error= 'Unable to Create Sales Invoice: ' + str(e), doc="Bill", doc_name=bill_number)
        return status

    def get_skip_invoice_customer(self):
        return frappe.get_all('Customer',filters = {'custom_skip_invoice_creation':1},pluck = 'name')


@ChunkOrchestrator.update_chunk_status
def create_and_cancel_sales_invoices(args: dict, new_bills: list, cancelled_bills: list) -> str:
    try:
        ChunkOrchestrator.process(SalesInvoiceCreator().cancel_sales_invoice, step_id=args["step_id"],
                                  cancelled_bills=cancelled_bills)
        ChunkOrchestrator().process(SalesInvoiceCreator().process, step_id=args["step_id"], is_enqueueable=True,
                                    chunk_size=args["chunk_size"], data_var_name="bill_numbers", queue=args["queue"],
                                    is_async=True, timeout=18000, bill_numbers=new_bills)
        return "Processed"
    except Exception as e:
        log_error(error=e, doc="Bill")
        return "Error"

@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    cancelled_bills = frappe.get_list('Bill', filters={'status': 'CANCELLED', 'invoice_status': 'RAISED'},
                                      pluck='name')
    new_bills = frappe.get_list('Bill', filters={'invoice': '', 'status': ['!=', 'CANCELLED AND DELETED']},
                                pluck='name')
    ChunkOrchestrator().process(create_and_cancel_sales_invoices, step_id=args["step_id"], new_bills=new_bills,
                                cancelled_bills=cancelled_bills)