import frappe
from agarwals.utils.adjust_bill import JournalUtils
from datetime import datetime

@frappe.whitelist()
def writeback():
    jv = JournalUtils()
    je = create_journal_entry("Journal Entry","2024-05-02", "fgh3254dgkdgj354768")
    append_child_table = add_account_entries(je,"GOPALAPURAM - 10010200021155 - A","WriteBack - A", 7000)
    jv.save_je(append_child_table)


def add_account_entries(je, from_account, to_account, amount):
        je.append('accounts', {
                'account': from_account,
                'credit_in_account_currency': amount,
                'user_remark': from_account
        })
        je.append('accounts', {
                'account': to_account,
                'debit_in_account_currency': amount,
                'user_remark': to_account,
        })
        return je

def create_journal_entry(type, date, ref_no):
        je = frappe.new_doc('Journal Entry')
        je.voucher_type = type
        je.posting_date = datetime.now()
        je.reference_number = ref_no
        je.reference_date = datetime.now()
        return je