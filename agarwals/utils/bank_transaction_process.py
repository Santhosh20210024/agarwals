import frappe


def create_bank_transaction(transaction_list):
    
    for transaction in transaction_list:
        bank_transaction_doc = frappe.new_doc('Bank Transaction')
        try:
            bank_transaction_doc.date = transaction.get('date')
            bank_transaction_doc.status = transaction.get('transaction_status')
            bank_transaction_doc.bank_account = transaction.get('bank_account')
            bank_transaction_doc.deposit = transaction.get('deposit')
            bank_transaction_doc.withdrawal = transaction.get('withdrawal')
            bank_transaction_doc.currency = 'INR'
            bank_transaction_doc.description = transaction.get('description')
            if transaction.get('update_reference_number') != None:
                bank_transaction_doc.reference_number = transaction.get('update_reference_number')
            else:
                bank_transaction_doc.reference_number = transaction.get('reference_number')
            bank_transaction_doc.unallocated_amount = transaction.get('deposit')
            bank_transaction_doc.submit()

            # transaction status
            transaction_doc = frappe.get_doc('Bank Transaction Stagging', transaction.name )
            if transaction.get('reference_number') == '0':
                transaction_doc.reference_number = bank_transaction_doc.name
                transaction_doc.status = 'Warning'
                transaction_doc.remarks = 'System Generated Reference Number'
            else:
                transaction_doc.status = "Processed"
            transaction_doc.save()

            frappe.db.commit()

        except Exception as e:
            transaction_doc = frappe.get_doc('Bank Transaction Stagging', transaction.name )
            transaction_doc.status = "Error"
            transaction_doc.remarks = str(e)
            transaction_doc.save()


def is_document_naming_rule(doctype):
    if len(frappe.get_list("Document Naming Rule", filters = {'document_type': doctype})) < 1:
        return False
    return True

@frappe.whitelist()
def process(tag):
    if not is_document_naming_rule('Bank Transaction'):
        frappe.msgprint("Document Naming Rule is not set for the Bank Transaction")
        return
    
    _transaction = [] 
    for transaction in frappe.get_all( 'Bank Transaction Stagging',filters = { '_user_tags' : ['like', f'%{tag}%'], 'status' : ['!=', 'Processed'] }, fields = "*" ):
        if transaction.status == "Warning":
            if transaction.get('update_reference_number') != None and transaction.retry == 1:
                _transaction.append(transaction)
        if transaction.status == 'Error':
            if transaction.retry == 1:
                _transaction.append(transaction)
        else:
            _transaction.append(transaction)
    
    create_bank_transaction(_transaction)

    return "Success"


    

