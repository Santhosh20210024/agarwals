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
