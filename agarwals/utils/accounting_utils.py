import frappe
from datetime import date

def is_accounting_period_exist(posting_date):
    return frappe.db.sql("""Select name from `tabAccounting Period` where %(date)s between start_date and end_date""", values={'date': posting_date}, as_dict = True)

def update_posting_date(_date):
    """Updates the posting date based on whether the accounting period exists"""
    if is_accounting_period_exist(_date.strftime("%Y-%m-%d")):
        return _date.today().strftime("%Y-%m-%d")
    else:
        return _date.strftime("%Y/%m/%d")