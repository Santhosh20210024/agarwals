import frappe
import traceback
from datetime import datetime as dt

TAG = 'Credit Payment'
ERROR_LOG = { 
    'E100': 'E100: Duplicate Reference Number',
    'E101': 'E101: Date is mandatory',
    'E102': 'E102: Both Deposit and Withdrawn should not be empty',
    'E103': 'E103: Should verify the reference number',
    'E104': 'E104: Previously processed and already Reconciled Bank Transaction',
    'E105': 'E105: Invalidate Update Reference Number'
}

def check_warning(trans_doc, transaction, bnk_trans_ref ): 
    if transaction.get('reference_number') == '0' or len(transaction.get('reference_number')) < 1:
        trans_doc.reference_number = bnk_trans_ref 
        trans_doc.staging_status = "Warning"
        trans_doc.remarks = "System Generated Reference Number"
    else:
        trans_doc.staging_status = "Processed"
        trans_doc.remarks = ""
        trans_doc.retry = 0

def create_bank_trans_doc(transaction, update_reference_number = None):
    reference_number = transaction.get('reference_number') if update_reference_number is None else update_reference_number
    bank_trans_doc = frappe.new_doc('Bank Transaction')
    bank_trans_doc.date = transaction.get('date')
    bank_trans_doc.status = transaction.get('transaction_status')
    bank_trans_doc.bank_account = transaction.get('bank_account')
    bank_trans_doc.deposit = transaction.get('deposit')
    bank_trans_doc.Withdrawn = transaction.get('Withdrawn')
    bank_trans_doc.currency = 'INR'
    bank_trans_doc.description = transaction.get('description')
    bank_trans_doc.reference_number = reference_number
    bank_trans_doc.unallocated_amount = transaction.get('deposit')
    bank_trans_doc.submit()
    frappe.db.commit()

    if reference_number == '0':
        return bank_trans_doc.name
    
    if not update_reference_number:
        return reference_number
    
def save_trans_doc(transaction):
    transaction.save()
    frappe.db.commit()
 
def delete_corrs_doc(doctype_name, doc_name):
    frappe.get_doc(doctype_name, doc_name).cancel()
    frappe.delete_doc(doctype_name, doc_name)
    frappe.db.commit()

def create_bank_transaction(transaction_list):
    for transaction in transaction_list:
        trans_doc = frappe.get_doc('Bank Transaction Staging', transaction.name)

        try:
            # layer level throws
            if transaction.get('date') == None:
                trans_doc.staging_status = 'Error'
                trans_doc.error = ERROR_LOG['E101']
                trans_doc.retry = 0
                save_trans_doc(trans_doc)
                continue

            if int(transaction.get('deposit')) == 0 and int(transaction.get('withdrawal')) == 0:
                trans_doc.staging_status = 'Error'
                trans_doc.error = ERROR_LOG['E102']
                trans_doc.retry = 0
                save_trans_doc(trans_doc)
                continue
                        
            if int(transaction.get('deposit')) == 0 and int(transaction.get('withdrawal')) != 0:
                trans_doc.staging_status = 'Withdrawn'
                trans_doc.remark = 'Withdrawn case'
                trans_doc.retry = 0
                save_trans_doc(trans_doc)
                continue

            if transaction.retry != 1 and transaction.get('update_reference_number') is None:
                if transaction.get('reference_number') != None and len(transaction.get('reference_number').strip().lstrip('0')) < 5:
                    if transaction.get('reference_number') != 0:
                        trans_doc.staging_status = 'Error'
                        trans_doc.error = ERROR_LOG['E103']
                        trans_doc.retry = 0
                        save_trans_doc(trans_doc)
                        continue

            if transaction.get('update_reference_number') != None and transaction.get('retry') == 1:
                bank_trans_doc = frappe.get_doc('Bank Transaction', transaction.reference_number)

                if int(bank_trans_doc.allocated_amount) == 0: # status sometimes ambiguous so go with allocated amount
                    delete_corrs_doc('Bank Transaction', transaction.get('reference_number'))
                    if transaction.get('update_reference_number') != None and len(transaction.get('update_reference_number').strip().lstrip('0')) < 5:
                        trans_doc.staging_status = 'Error'
                        trans_doc.error = ERROR_LOG['E105']
                        trans_doc.retry = 0  
                        save_trans_doc(trans_doc)
                        continue
                        
                    create_bank_trans_doc(transaction, transaction.get('update_reference_number'))
                    trans_doc = frappe.get_doc('Bank Transaction Staging', transaction.name )
                    trans_doc.previous_utr = transaction.get('reference_number')
                    trans_doc.reference_number = transaction.get('update_reference_number')
                    trans_doc.staging_status = "Processed"
                    trans_doc.remarks = 'User Generated Reference Number'
                    trans_doc.retry = 0
                    trans_doc.save()
                    frappe.db.commit()

                else:
                    trans_doc.staging_status = "Error"
                    trans_doc.error = ERROR_LOG['E104']
                    trans_doc.retry = 0
                    trans_doc.save()
                    frappe.db.commit()

            elif transaction.get('retry') == 1:
                # paid date
                if transaction.get('date') is not None:
                    if transaction.reference_number is None:
                        transaction.reference_number = '0'

                    bnk_trans_ref = create_bank_trans_doc(transaction)
                    check_warning(trans_doc, transaction, bnk_trans_ref)
                    trans_doc.save()
                    frappe.db.commit()
                    # if there is any update in future need to resolve those error cases

            else: 
                if transaction.reference_number is None:  
                    # additional check for the blank reference_number field
                    transaction.reference_number = '0'

                bnk_trans_ref = create_bank_trans_doc(transaction)
                check_warning(trans_doc, transaction, bnk_trans_ref)
                trans_doc.save()
                frappe.db.commit()
            
        except Exception as e:
            trans_doc = frappe.get_doc('Bank Transaction Staging', transaction['name'] )
            trace_info = str(traceback.format_exc()).split(':')[-1]

            # duplicate entry
            if 'Duplicate entry' in trace_info:
                trans_doc.staging_status = "Error"
                trans_doc.error = ERROR_LOG['E100']
                trans_doc.remark = trace_info
            else:
                trans_doc.remark = trace_info

            trans_doc.save()
            frappe.db.commit()

def staging_batch_operation(chunk):
    create_bank_transaction(chunk)

def tag_skipped():
    frappe.db.sql("""
        UPDATE `tabBank Transaction Staging` set staging_status = 'Skipped' where staging_status = 'Open' and tag is NULL
        """)
    frappe.db.commit()

def bank_transaction_process(tag):
    pending_transaction = [] 
    for transaction in frappe.get_all( 'Bank Transaction Staging', filters = { 'tag' : tag, 'staging_status' : ['!=', 'Processed'] }, fields = "*" ):
        if transaction.staging_status == "Warning":
            if transaction.get('update_reference_number') != None and transaction.retry == 1:
                pending_transaction.append(transaction)
                continue
        if transaction.staging_status == 'Error':
            if transaction.retry == 1:
                pending_transaction.append(transaction)
                continue
        if transaction.staging_status == 'Open': 
            pending_transaction.append(transaction)

    # also Check if there is any change in the processed entrys retry
    for transaction in frappe.get_all( 'Bank Transaction Staging', filters = { 'staging_status' : ['=', 'Processed'], 'update_reference_number' : ['!=', None], 'retry': 1}):
        pending_transaction.append(transaction)
    
    chunk_size = 10000
    for i in range(0, len(pending_transaction), chunk_size):
        frappe.enqueue(staging_batch_operation, queue='long', is_async=True, timeout=18000, chunk = pending_transaction[i:i + chunk_size])

def change_matched_items(ref_no):

    # Journal Entry # Later, it will removed.
    for item in frappe.get_list('Journal Entry', filters={'cheque_no':ref_no, 'docstatus':['!=', '2']}):
        je_doc = frappe.get_doc('Journal Entry', item['name'])
        je_doc.add_comment(
                    text= ("Journal Entry Cancelled due to Withdrawn Case")
                )
        je_doc.cancel()
        frappe.db.commit()

    # Payment Entry # Need to check
    for item in frappe.get_list('Payment Entry', filters = {'reference_no':ref_no, 'status':['!=', 'Cancelled']}):
        pe_doc = frappe.get_doc('Payment Entry', item['name'])
        pe_doc.add_comment(
                    text= ("Payment Entry Cancelled due to Withdrawn Case")
                )
        pe_doc.cancel()
        frappe.db.commit()
    
    ref_no = str(ref_no).strip().lstrip('0')
    advice_item_cg = frappe.get_list('Settlement Advice', filters = {'final_utr_number': ref_no, 'status': 'Processed'}, pluck = 'name')
    advice_item_ag = [ se_item['name'] for se_item in frappe.get_list('Settlement Advice', filters = {'status': 'Processed'}, fields = ['name', 'utr_number'])
                       if se_item['utr_number'].strip().lstrip('0') == ref_no ]
    
    advice = set(advice_item_cg + advice_item_ag)
    for item in advice:
        frappe.db.sql("""
                      DELETE from `tabMatch Log` where parent = %(advice)s
                      """, values = { 'advice': item})
        frappe.db.set_value('Settlement Advice', item, 'status', 'Open')
        frappe.db.set_value('Settlement Advice', item, 'remark', '')
        frappe.get_doc('Settlement Advice', item).add_comment(
                    text= ("Advice status is changed due to the Withdrawn Case")
                )
        frappe.db.commit()

def compare_date(cr_date, dt_date):
    return True if cr_date <= dt_date else False    

def check_withdrawn_je():
    wd_list = frappe.db.sql("""select * from `tabBank Transaction Staging` bts  
                               where bts.reference_number in ( select name from `tabBank Transaction` where status != 'Cancelled') and bts.withdrawal != 0
                            """, as_dict = True)
    for wd in wd_list:
        doc = frappe.get_doc('Bank Transaction', wd.get('reference_number'))
        if doc:
            if doc.deposit == wd.get('withdrawal') and compare_date(doc.date, wd.date):

                # Due to payment entry, need to change it in corresponding manner.
                frappe.db.sql("""
                              DELETE from `tabTransaction` where reference_number = %(utr_number)s
                              """, values={ 'utr_number' : doc.reference_number })
                frappe.db.commit()
                
                bnk_doc = frappe.get_doc('Bank Transaction', doc.name)
                bnk_doc.remove_payment_entries()
                bnk_doc.add_comment(
                    text= ("Bank Transaction Cancelled due to Withdraw Case")
                    )
                bnk_doc.save()
                frappe.db.commit()

                change_matched_items(doc.name)
                bnk_doc.cancel()
                frappe.db.commit()

def is_document_naming_rule(doctype):
    if len(frappe.get_list("Document Naming Rule", filters = {'document_type': doctype})) < 1:
        return False
    return True

@frappe.whitelist()
def process(tag):
    if not is_document_naming_rule('Bank Transaction'):
        frappe.msgprint("Document Naming Rule is not set for the Bank Transaction")
        return

    check_withdrawn_je() # cancellation process
    tag_skipped() # tag the skip status
    bank_transaction_process(tag) # bank transaction process
