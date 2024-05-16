import frappe
from agarwals.utils.adjust_bill import JournalUtils
from datetime import datetime

@frappe.whitelist()
def create_writeback_jv():
    writeback_list = get_doc_list("Write Back", {"status": "Created"}, ["*"])
    for writeback in writeback_list:
        try:
            bank_transaction = frappe.get_doc("Bank Transaction", writeback.reference_number)
            if bank_transaction.status == "Unreconciled" or "Pending":
                if bank_transaction.unallocated_amount <= int(writeback.unallocated_amount) + 10:
                    file_upload_name = writeback.file_upload
                    file_upload_list = get_doc_list("File upload",{"name":file_upload_name},["*"])
                    posting_date = file_upload_list[0].wb_date
                    account_name = writeback.bank_account
                    company_account_list = get_doc_list("Bank Account",{"name":account_name},["*"])
                    company_account = company_account_list[0].account
                    jv = JournalUtils()
                    je = create_journal_entry("Journal Entry", str(posting_date), writeback.reference_number)
                    credit_data, debit_data = set_writeback_account_data(writeback, company_account)
                    append_child_table = add_account_entries(je,credit_data, debit_data)
                    jv.save_je(append_child_table)
                    writeback_doc = frappe.get_doc("Write Back", writeback.name)
                    writeback_doc.status = "Processed"
                    writeback_doc.save()
                else:
                    log_error('Journal Entry', writeback.name,"Bank Transaction is Fully Reconciled")
                    update_doc_status("Write Back", writeback.name, "Error")
            else:
                log_error('Journal Entry', writeback.name, "Unallocated amount in Bank Transaction is higher than the amount given in Write Back")
                update_doc_status("Write Back", writeback.name, "Error")
        except Exception as e:
            log_error('Journal Entry',writeback.name,e)
            update_doc_status("Write Back", writeback.name, "Error")



def log_error(doctype,ref_name,error_message):
    error_log = frappe.new_doc('Error Record Log')
    error_log.set('doctype_name', doctype)
    error_log.set('reference_name', ref_name)
    error_log.set('error_message', '' + str(error_message))
    error_log.save()

def update_doc_status(doctype,docname, status):
    document = frappe.get_doc(doctype, docname)
    document.status = status
    document.save()
def set_writeback_account_data(writeback,company_account):
    credit_data = {
                'account': company_account,
                'region':writeback.region,
                'entity':writeback.entity,
                'branch_type':writeback.branch_type,
                'credit_in_account_currency': writeback.deposit,
                'user_remark': f"writeback_name:{writeback.name},file_upload_name:{writeback.file_upload},bank_transaction:{writeback.reference_number}"}
    debit_data = {
                'account': "WriteBack - A",
                'debit_in_account_currency': writeback.deposit,
                'user_remark': f"writeback_name:{writeback.name},file_upload_name:{writeback.file_upload},bank_transaction:{writeback.reference_number}"}
    return credit_data, debit_data
def add_account_entries(je,credit_data, debit_data):
        je.append('accounts', credit_data)
        je.append('accounts', debit_data)
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

@frappe.whitelist()
def create_writeoff_jv():
    writeoff_list = get_doc_list("Write Off", {"status": "Created"}, ["*"])
    for writeoff in writeoff_list:
        try:
            sales_invoice = frappe.get_doc("Sales Invoice", writeoff.name)
            if sales_invoice.status == "Unpaid" or "Partly Paid" :
                if sales_invoice.outstanding_amount <= int(writeoff.outstanding_amount) + 10:
                    file_upload_name = writeoff.file_upload
                    file_upload_list = get_doc_list("File upload",{"name":file_upload_name},["*"])
                    posting_date = file_upload_list[0].wo_date
                    debt_account = "Debtors - A"
                    jv = JournalUtils()
                    je = create_journal_entry("Journal Entry", str(posting_date), writeoff.bill_no)
                    je.bill_no = writeoff.name
                    je.bill_date = writeoff.bill_date
                    credit_data, debit_data = set_writeoff_account_data(writeoff, debt_account)
                    append_child_table = add_account_entries(je, credit_data, debit_data)
                    jv.save_je(append_child_table)
                    writeoff_doc = frappe.get_doc("Write Off", writeoff.name)
                    writeoff_doc.status = "Processed"
                    writeoff_doc.save()
                else:
                    log_error('Journal Entry', writeoff.name,
                              "Sales Invoice Tagged to bill is Paid or Cancelled")
                    update_doc_status("Write Back", writeoff.name, "Error")
            else:
                log_error('Journal Entry', writeoff.name, "Unallocated Amount in Sales Invoice is Higher than the Amount given in Write Off")
                update_doc_status("Write Back", writeoff.name, "Error")
        except Exception as e:
            log_error("Journal Entry", writeoff.name,e)
            update_doc_status("Write Off", writeoff.name, "Error")

def set_writeoff_account_data(writeoff,debt_account):
    credit_data = {
                'account': debt_account,
                'party_type': "Customer",
                'party': writeoff.customer,
                'region':writeoff.region,
                'entity':writeoff.entity,
                'branch':writeoff.branch,
                'credit_in_account_currency': writeoff.outstanding_amount,
                'user_remark': f"writeoff_name:{writeoff.name},file_upload_name:{writeoff.file_upload}"
    }
    debit_data = {
                'account': "Write Off - A",
                'debit_in_account_currency': writeoff.outstanding_amount,
                'user_remark': f"writeoff_name:{writeoff.name},file_upload_name:{writeoff.file_upload}"
    }
    return credit_data, debit_data