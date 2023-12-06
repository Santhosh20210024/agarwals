# bank transations -> settlement advices -> debtors -> payment entry
import frappe

def get_bank_transactions(skip_status):
    bank_transactions_list = frappe.db.get_list('Bank Transaction',filters={'status':['!=',skip_status]}, fields="*")
    return bank_transactions_list

# def get_settlement_advices(skip_status):
#     settlement_advice_list = frappe.db.get_list('Settlement Advice',filters={'status':['!=',skip_status]}, fields=['name','status','claim_no','utr_number','claim_amount','tds_amount'])
#     return settlement_advice_list

def get_debtors_report_details(claim_id):
    corres_debtors_report = frappe.db.get_list('Debtors Report',filters={'claim_id':claim_id},fields="*")
    return corres_debtors_report

def tagging_payment_invoice_reference(payment_entry, invoice_no, allocated_amount):
    reference_item = {
            'reference_doctype': 'Sales Invoice',
            'reference_name': invoice_no,
            'allocated_amount': allocated_amount
        }
    payment_entry.append('references', reference_item)
    return payment_entry

def payment_entry_doc_creation(invoice_no, customer_name, claim_amount, bank_account, utr_number, date):
    _payment_entry = frappe.new_doc('Payment Entry')
    _payment_entry.mode_of_payment = 'Bank Draft'
    _payment_entry.party_type = 'Customer'
    _payment_entry.party = customer_name
    _payment_entry.paid_from = 'Debtors - A'
    _payment_entry.paid_to = bank_account
    _payment_entry.paid_amount = claim_amount
    _payment_entry.reference_no = utr_number
    _payment_entry.date = date
    _payment_entry.save()

    if _payment_entry.name:
        payment_entry = tagging_payment_invoice_reference(_payment_entry, invoice_no, claim_amount)
        payment_entry.submit()

def main_process():
    bank_transactions = get_bank_transactions('reconciled') #1

    for transaction in bank_transactions:
        corresponding_settlemet_advices  = frappe.db.get_list('Settlement Advice',filter={'utr_number':transaction.reference_number,'status':['!=','Closed']},fields='*')
        for settlement_item in corresponding_settlemet_advices:
                debtors_report_item = get_debtors_report_details(settlement_item['claim_no'])
                if debtors_report_item.customer_name:
                    payment_entry_doc_creation(debtors_report_item.name, debtors_report_item.customer_name, settlement_item['settlement_amount'], transaction.bank_account, transaction.reference_number, transaction.date)
                    
                    # Validate if the transaction amount matches the claim amount
                    if transaction.amount >= settlement_item['claim_amount']:
                        settlement_doc = frappe.get_doc('Settlement Advice', settlement_item['name'])
                        settlement_doc.status = "Closed"
                        settlement_doc.save()

@frappe.whitelist()
def matching_process():
    main_process()