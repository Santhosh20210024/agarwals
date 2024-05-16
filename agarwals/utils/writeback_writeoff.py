import frappe
from agarwals.utils.adjust_bill import JournalUtils
from datetime import datetime

@frappe.whitelist()
def journal_entry_creation():
    writeback_list = get_doc_list("Write Back", {"status":["=",["Created","Error"]]}, ["*"])
    for writeback in writeback_list:
        try:
            file_upload_name = writeback.file_upload
            file_upload_list = get_doc_list("File upload",{"name":file_upload_name},["*"])
            posting_date = file_upload_list[0].wb_date
            account_name = writeback.bank_account
            company_account_list = get_doc_list("Bank Account",{"name":account_name},["*"])
            company_account = company_account_list[0].account
            jv = JournalUtils()
            je = create_journal_entry("Journal Entry", str(posting_date), writeback.reference_number)
            append_child_table = add_account_entries(je, writeback, company_account)
            jv.save_je(append_child_table)
            writeback.status = "Processed"
            writeback.save()
        except Exception as e:
            print("error", e)


def add_account_entries(je, writeback,company_account):
        je.append('accounts', {
                'account': company_account,
                'region':writeback.region,
                'reference_type':'Asset',
                'entity':writeback.entity,
                'branch_type':writeback.branch_type,
                'credit_in_account_currency': writeback.deposit,
                'user_remark': f"writeback_name:{writeback.name},file_upload_name:{writeback.file_upload},bank_transaction:{writeback.reference_number}"})
        je.append('accounts', {
                'account': "WriteBack - A",
                'region': writeback.region,
                'entity': writeback.entity,
                'reference_type': 'Asset',
                'branch_type': writeback.branch_type,
                'debit_in_account_currency': writeback.deposit,
                'user_remark': f"writeback_name:{writeback.name},file_upload_name:{writeback.file_upload},bank_transaction:{writeback.reference_number}"})
        return je

def create_journal_entry(type, date, ref_no):
        je = frappe.new_doc('Journal Entry')
        je.voucher_type = type
        je.posting_date = date
        je.cheque_no = ref_no
        je.cheque_date = datetime.now()
        return je
def get_doc_list(doctype,filters,fields):
    doc_list = frappe.get_all(doctype,filters,fields)
    return doc_list