# bank transations -> settlement advices -> debtors -> payment entry
import frappe

def get_bank_transactions(skip_status):
    bank_transactions_list = frappe.db.get_list('Bank Transaction',filters={'status':['!=',skip_status]}, fields="*")
    return bank_transactions_list

def get_settlement_advices(skip_status):
    settlement_advice_list = frappe.db.get_list('Settlement Advice',filters={'status':['!=',skip_status]}, fields=['name','status','claim_no','utr_number','claim_amount','tds_amount'])
    return settlement_advice_list

def get_debtors_report_details(claim_id):
    corres_debtors_report = frappe.db.get_list('Debtors Report',filters={'claim_id':claim_id},fields="*")
    return corres_debtors_report

def tagging_payment_invoice_reference(invoice_no,payment_entry_id):
    _payment_entry_reference = frappe.new_doc('Payment Entry Reference')
    _payment_entry_reference.reference_doctype = 'Sales Invoice'
    _payment_entry_reference.reference_type = invoice_no
    _payment_entry_reference.parent = payment_entry_id
    _payment_entry_reference.save()

def payment_entry_doc_creation(invoice_no, customer_name, claim_amount, bank_account, utr_number, date):
    _payment_entry = frappe.new_doc('Payment Entry')
    _payment_entry.mode_of_payment = 'Bank Draft'
    _payment_entry.party_type = 'Customer'
    _payment_entry.party = customer_name
    _payment_entry.account_paid_from = 'Debtors - A'
    _payment_entry.account_paid_to = bank_account
    _payment_entry.paid_amount = claim_amount
    _payment_entry.reference_no = utr_number
    _payment_entry.date = date
    _payment_entry.save()

    if _payment_entry.name:
        tagging_payment_invoice_reference(invoice_no,_payment_entry.name)
        _payment_entry.submit()

def main_process():
    bank_transactions = get_bank_transactions('reconciled') #1
    settlement_advice = get_settlement_advices('Closed') #2

    # Consider the time complexity
    for transaction in bank_transactions:
        for settlement_item in settlement_advice:
            if transaction.reference_number == settlement_item.utr_number:
                debtors_report_item = get_debtors_report_details(settlement_item['claim_no'])[0] #3
                if debtors_report_item.customer_name:
                    payment_entry_doc_creation(debtors_report_item.name, debtors_report_item.customer_name, settlement_item['claim_amount'], transaction.bank_account, transaction.reference_number, transaction.date)
                    
                    # Validate if the transaction amount matches the claim amount
                    if transaction.amount >= settlement_item['claim_amount']:
                        settlement_doc = frappe.get_doc('Settlement Advice', settlement_item['name'])
                        settlement_doc.status = "Closed"
                        settlement_doc.save()

@frappe.whitelist()
def matching_process():
    main_process()