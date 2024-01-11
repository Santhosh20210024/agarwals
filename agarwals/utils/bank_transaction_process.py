import frappe
import traceback

TAG = 'Insurance'

def create_bank_transaction(transaction_list):
 
    for transaction in transaction_list:
        try:
            # Update record
            if transaction.get('update_reference_number') != None and transaction.get('retry') == 1: # tested # done
                bank_transaction_doc = frappe.get_doc('Bank Transaction', transaction.reference_number) 
                frappe.db.sql("""
                             update `tabBank Transaction` set name = %(name)s, reference_number = %(name)s where name = %(reference_number)s   
                             """, values={'name': transaction.get('update_reference_number'), 'reference_number': transaction.reference_number}) # check done
                
                bank_transaction_doc.reference_number = transaction.get('update_reference_number')
                bank_transaction_doc.db_update()
                
                transaction_doc = frappe.get_doc('Bank Transaction Staging', transaction.name )
                transaction_doc.previous_utr = transaction.get('reference_number')
                transaction_doc.reference_number = transaction.get('update_reference_number')
                transaction_doc.staging_status = "Processed"
                transaction_doc.remarks = 'User Generated Reference Number'
                transaction_doc.retry = 0
                transaction_doc.save()

            else:
                # New record
                bank_transaction_doc = frappe.new_doc('Bank Transaction')
                bank_transaction_doc.date = transaction.get('date')
                bank_transaction_doc.status = transaction.get('transaction_status')
                bank_transaction_doc.bank_account = transaction.get('bank_account')
                bank_transaction_doc.deposit = transaction.get('deposit')
                bank_transaction_doc.withdrawal = transaction.get('withdrawal')
                bank_transaction_doc.currency = 'INR'
                bank_transaction_doc.description = transaction.get('description')
                bank_transaction_doc.reference_number = transaction.get('reference_number')
                bank_transaction_doc.unallocated_amount = transaction.get('deposit')
                bank_transaction_doc.submit()
                frappe.db.commit()

                # Transaction status
                transaction_doc = frappe.get_doc('Bank Transaction Staging', transaction['name'] )
                if transaction.get('reference_number') == '0': # tested
                    transaction_doc.reference_number = bank_transaction_doc.name # tested
                    transaction_doc.staging_status = "Warning"
                    transaction_doc.remarks = "System Generated Reference Number" # tested
                else:
                    transaction_doc.staging_status = "Processed"
                    transaction_doc.remarks = ""
                transaction_doc.save()
            frappe.db.commit()
            
        except Exception as e:
            transaction_doc = frappe.get_doc('Bank Transaction Staging', transaction['name'] )
            transaction_doc.staging_status = "Error"
            trace_info = traceback.format_exc()
            transaction_doc.remarks = str(trace_info).split(':')[-1]
            transaction_doc.save()
            frappe.db.commit()

def staging_batch_operation(chunk):
    create_bank_transaction(chunk)

def is_document_naming_rule(doctype):
    if len(frappe.get_list("Document Naming Rule", filters = {'document_type': doctype})) < 1:
        return False
    return True

@frappe.whitelist()
def process(tag):
    if not is_document_naming_rule('Bank Transaction'):
        frappe.msgprint("Document Naming Rule is not set for the Bank Transaction")
        return
    
    pending_transaction = [] # tested
    for transaction in frappe.get_all( 'Bank Transaction Staging', filters = { 'tag' : tag, 'staging_status' : ['!=', 'Processed'] }, fields = "*" ):
        if transaction.staging_status == "Warning":
            if transaction.get('update_reference_number') != None and transaction.retry == 1: # tested
                pending_transaction.append(transaction)
                continue
        if transaction.staging_status == 'Error': # test
            if transaction.retry == 1:
                pending_transaction.append(transaction)
                continue
        if transaction.staging_status == 'Open':
            pending_transaction.append(transaction)

    chunk_size = 1000
    for i in range(0, len(pending_transaction), chunk_size):
        frappe.enqueue(staging_batch_operation, queue='long', is_async=True, timeout=18000, chunk = pending_transaction[i:i + chunk_size])