import frappe

def is_accounting_period_exist(posting_date):
    return frappe.db.sql("""Select name from `tabAccounting Period` where %(date)s between start_date and end_date""", values={'date': posting_date}, as_dict = True)
