from agarwals.utils.transformer import BillTransformer,ClaimbookTransformer,BankTransformer
import frappe

@frappe.whitelist()
def run_transform_process(type):
    if type == "debtors":
        try:
            BillTransformer().process()
            return "Success"
        except Exception as e:
            return e
    elif type == "claimbook":
        try:
            ClaimbookTransformer().process()
            return "Success"
        except Exception as e:
            return e
    # elif type =="Settlement":
    #     try:
    #         SettlementTransformer().process()
    #         return "Success"
    #     except Exception as e:
    #         return e
    elif type =="transaction":
        try:
            BankTransformer().process()
            return "Success"
        except Exception as e:
            return e

@frappe.whitelist()
def create_sales_invoice():
    try:
        cancelled_bills = frappe.get_list('Bill', filters={'status': 'CANCELLED', 'invoice_status': 'RAISED'},
                                          pluck='name')
        SalesInvoiceCreator().cancel_sales_invoice(cancelled_bills)
        new_bills = frappe.get_list('Bill', filters= {'invoice':''})
        SalesInvoiceCreator().enqueue_job(new_bills)
    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('error_message', e)
        error_log.save()