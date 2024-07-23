import frappe
from agarwals.reconciliation.step.adjust_bill import JournalUtils
from datetime import datetime
from agarwals.utils.error_handler import log_error as error_handler

@frappe.whitelist()
def create_writeback_jv():
    writeback_list = get_doc_list("Write Back", {"status": "Created"}, ["*"])
    for writeback in writeback_list:
        try:
            bank_transaction = frappe.get_doc("Bank Transaction", writeback.reference_number)
            if bank_transaction.status == "Unreconciled" or "Pending":
                if bank_transaction.unallocated_amount <= int(writeback.unallocated_amount) + 10:
                    if bank_transaction.unallocated_amount != 0:
                        # init save_je class
                        jv = JournalUtils()
                        # get file_upload_list
                        file_upload_list = get_doc_list("File upload",{"name":writeback.file_upload},["*"])
                        # get posting and debt_account
                        posting_date = file_upload_list[0].wb_date
                        account_name = writeback.bank_account
                        # get company_account
                        company_account_list = get_doc_list("Bank Account",{"name":account_name},["*"])
                        company_account = company_account_list[0].account
                        # init je
                        je = create_journal_entry("Journal Entry", str(posting_date), "WB", bank_transaction)
                        # append account_details
                        credit_data, debit_data = set_writeback_account_data(bank_transaction, company_account,bank_transaction.unallocated_amount)
                        append_child_table = add_account_entries(je,credit_data, debit_data)
                        # save jv
                        jv.save_je(append_child_table, writeback)
                        # update document
                            #banktransaction
                        reconcile_document("Bank Transaction",writeback.reference_number,"Journal Entry",je.name,bank_transaction.unallocated_amount,"payment_entries")
                            #writeback
                        writeback_doc = frappe.get_doc("Write Back", writeback.name)
                        writeback_doc.status = "Processed"
                        writeback_doc.save()
                    else:
                        log_error('Journal Entry', writeback.name, "Bank Transaction amount is equal to 0")
                        update_doc_status("Write Back", writeback.name, "Error")
                else:
                    log_error('Journal Entry', writeback.name,"Bank Transaction is Fully Reconciled")
                    update_doc_status("Write Back", writeback.name, "Error")
            else:
                log_error('Journal Entry', writeback.name, "Unallocated amount in Bank Transaction is higher than the amount given in Write Back")
                update_doc_status("Write Back", writeback.name, "Error")
        except Exception as e:
            log_error('Journal Entry',writeback.name,e)
            update_doc_status("Write Back", writeback.name, "Error")




def reconcile_document(doctype, docname, payment_document,payment_entry,allocated_amount, child_table):
    bank_transaction_doc = frappe.get_doc(doctype, docname)
    bank_transaction_doc.append(child_table, {
        "payment_document": payment_document,
        "payment_entry": payment_entry,
        "allocated_amount": allocated_amount
    })
    bank_transaction_doc.save()


def log_error(doctype,ref_name,error_message):
    error_handler(error=str(error_message), doc=doctype, doc_name=ref_name)
    # error_log = frappe.new_doc('Error Record Log')
    # error_log.set('doctype_name', doctype)
    # error_log.set('reference_name', ref_name)
    # error_log.set('error_message', '' + str(error_message))
    # error_log.save()

def update_doc_status(doctype,docname, status):
    document = frappe.get_doc(doctype, docname)
    document.status = status
    document.save()

def set_writeback_account_data(bank_transaction,company_account, amount):
    credit_data = {

                'account' : company_account,
                'region' : bank_transaction.custom_region,
                'entity' : bank_transaction.custom_entity,
                'branch_type' : bank_transaction.custom_branch_type,
                'reference_type' : "Bank Transaction",
                'reference_name' : bank_transaction.name,
                'credit_in_account_currency' : amount
               }
    debit_data = {
                'account' : "WriteBack - A",
                'region' : bank_transaction.custom_region,
                'entity' : bank_transaction.custom_entity,
                'branch_type' : bank_transaction.custom_branch_type,
                'debit_in_account_currency' : amount
                }
    return credit_data, debit_data

def add_account_entries(je,credit_data, debit_data):
        je.append('accounts', credit_data)
        je.append('accounts', debit_data)
        return je

def create_journal_entry(type, posting_date, doctype, parent):
    je = frappe.new_doc('Journal Entry')
    je.name = f"{parent.name}-{doctype}"
    je.voucher_type = type
    je.posting_date = posting_date
    je.custom_party_type = "Customer"
    if doctype == "WB":
        je.custom_entity = parent.custom_entity
        je.custom_party = parent.party
        je.custom_party_group = parent.custom_party_group
        je.custom_branch_type = parent.custom_branch_type
        je.custom_utr_date = parent.date
        je.custom_region = parent.custom_region
        je.cheque_no = parent.name
        je.cheque_date = parent.date

    elif doctype == "WO":
        je.custom_sales_invoice = parent.name
        je.custom_entity = parent.entity
        je.custom_branch = parent.branch
        je.custom_bill_date = parent.posting_date
        je.custom_party = parent.customer
        je.custom_region = parent.region
        je.custom_party_group = parent.customer_group
        je.custom_branch_type = parent.branch_type

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
                    if sales_invoice.outstanding_amount != 0 :
                        #get_sales_invoice_date
                        sales_invoice_date = sales_invoice.posting_date
                        #init save_je class
                        jv = JournalUtils()
                        #get file_upload_list
                        file_upload_list = get_doc_list("File upload",{"name":writeoff.file_upload},["*"])
                        #get posting and debt_account
                        posting_date = file_upload_list[0].wo_date
                        debt_account = "Debtors - A"
                        #init je
                        je = create_journal_entry("Journal Entry", str(posting_date), "WO",sales_invoice)
                        je.bill_no = writeoff.name
                        je.bill_date = writeoff.bill_date
                        #append account_details
                        credit_data, debit_data = set_writeoff_account_data(sales_invoice, debt_account,sales_invoice.outstanding_amount)
                        append_child_table = add_account_entries(je, credit_data, debit_data)
                        #save jv
                        jv.save_je(append_child_table, writeoff)
                        #update document
                            #sales invoice
                        reconcile_document_writeoff("Sales Invoice",writeoff.name,"Journal Entry",je.name,sales_invoice.outstanding_amount,"custom_reference")
                            #writeoff
                        writeoff_doc = frappe.get_doc("Write Off", writeoff.name)
                        writeoff_doc.status = "Processed"
                        writeoff_doc.save()
                    else:
                        log_error('Journal Entry', writeoff.name,
                                  "Sales Invoice Amount is equal to 0")
                        update_doc_status("Write Off", writeoff.name, "Error")
                else:
                    log_error('Journal Entry', writeoff.name,
                              "Sales Invoice Tagged to bill is Paid or Cancelled")
                    update_doc_status("Write Off", writeoff.name, "Error")
            else:
                log_error('Journal Entry', writeoff.name, "Unallocated Amount in Sales Invoice is Higher than the Amount given in Write Off")
                update_doc_status("Write Off", writeoff.name, "Error")
        except Exception as e:
            log_error("Journal Entry", writeoff.name,e)
            update_doc_status("Write Off", writeoff.name, "Error")



def set_writeoff_account_data(sales_invoice,debt_account,amount):
    credit_data = {
                'account': debt_account,
                'party_type': "Customer",
                'party': sales_invoice.customer,
                'region':sales_invoice.region,
                'entity':sales_invoice.entity,
                'branch':sales_invoice.branch,
                'credit_in_account_currency': amount,
                'reference_type': 'Sales Invoice',
                'reference_name': sales_invoice.name

    }
    debit_data = {
                'account': "Write Off - A",
                'debit_in_account_currency': amount,
                'region': sales_invoice.region,
                'entity': sales_invoice.entity,
                'branch': sales_invoice.branch
    }
    return credit_data, debit_data



def reconcile_document_writeoff(doctype, docname, payment_document,payment_entry,allocated_amount, child_table):
    bank_transaction_doc = frappe.get_doc(doctype, docname)
    bank_transaction_doc.append(child_table, {
        "entry_type": payment_document,
        "entry_name": payment_entry,
        "writeoff_amount": allocated_amount
    })
    bank_transaction_doc.save()