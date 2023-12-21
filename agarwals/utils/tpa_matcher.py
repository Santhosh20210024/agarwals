import frappe
from frappe.utils import add_to_date
@frappe.whitelist()
def match_tpa():
    bills = frappe.get_list('Bill',filters = {'tpa':''},fields = '*')
    payers = frappe.get_list('Payer Alias', fields=['payer_name', 'payer_final_name'])

    try:
        for bill in bills:
            try:
                for payer in payers:
                    if bill.payer.strip().lower() == payer['payer_name'].strip().lower():
                        frappe.db.set_value('Bill',bill.bill_no,'tpa',payer['payer_final_name'])
                        break
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name','Bill')
                error_log.set('error_message',e)
                error_log.save()

        return "success"

    except Exception as e:
        return e

@frappe.whitelist()
def map_region():
    bills = frappe.get_list('Bill',filters = {'region':''},fields = '*')
    region_master = frappe.get_list('Branch Region List', fields = ['branch','region'])

    try:
        for bill in bills:
            try:
                for region in region_master:
                    branch = region['branch']
                    if bill.branch == region['branch']:
                        frappe.db.set_value('Bill',bill.bill_no,'region',region['region'])
                        break
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bill')
                error_log.set('error_message', e)
                error_log.save()

        return "success"

    except Exception as e:
        return e


@frappe.whitelist()
def create_sales_invoice():
    try:
        bills = frappe.get_list('Bill',filters = {'status':'RAISED','invoice':''},fields='*')
        for bill in bills:
            try:
                sales_invoice_existing = True if len(
                    frappe.get_list("Sales Invoice", filters={'name': bill.bill_no})) != 0 else False
                if not sales_invoice_existing:
                    sales_invoice = frappe.new_doc('Sales Invoice')
                    sales_invoice_item = [{'item_code': 'Claim', 'rate': bill.claim_amount, 'qty': 1}]
                    sales_invoice.set('bill_no', bill.bill_no)
                    sales_invoice.set('entity', bill.company)
                    sales_invoice.set('region', bill.region)
                    sales_invoice.set('cost_center', bill.cost_center)
                    sales_invoice.set('items', sales_invoice_item)
                    sales_invoice.set('customer', bill.tpa)
                    sales_invoice.set('set_posting_time',1)
                    sales_invoice.set('posting_date', bill.bill_date)
                    sales_invoice.set('due_date', bill.bill_date)
                    sales_invoice.save()
                    sales_invoice.submit()
                    frappe.db.set_value('Bill', bill.bill_no, 'invoice', sales_invoice.name)
                    frappe.db.commit()
                    print('Sales Invoice Created')
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bill')
                error_log.set('reference_name',bill.bill_no)
                error_log.set('error_message', e)
                error_log.save()

        return 'Success'

    except Exception as e:
        return e