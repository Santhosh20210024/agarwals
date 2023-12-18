# Bank Transations -> All Matched UTRs from settlement advices -> List of claimbook ( Claim ID ) -> List of Bill ( Bill No ) -> Journal Entry 

import frappe
from datetime import datetime

class BankTransactionWrapper():
    def __init__(self, bank_transaction):
        self.bank_transaction = bank_transaction
        self.available_amount = bank_transaction.deposit
        self.bank_account = frappe.db.get_value('Bank Account', self.bank_transaction.bank_account, 'account')

    def process(self):
        try:
            advices  = frappe.db.sql("""
                SELECT * FROM `tabSettlement Advice` WHERE utr_number = %(utr_number)s
                """, values = { 'utr_number' : self.bank_transaction.reference_number }, as_dict = 1 )
            
            # print(advices)
            if len(advices) < 1:
                return
            
            je = frappe.new_doc('Journal Entry')
            je.accounts = []

            for advice in advices:
                if not (advice.claim_id or advice.bill_no):
                    continue
                if self.available_amount <= 0:
                    break
                
                entry, tds_entry = self.create_payment_entry_item(advice)
                if entry:
                    je.append('accounts', entry)
                    if tds_entry:
                        je.extend('accounts', tds_entry)
                else:
                    continue

            allocated_amount = self.bank_transaction.deposit - self.available_amount
            asset_entry = {'account': self.bank_account, 'debit_in_account_currency': allocated_amount }
            
            je.append('accounts', asset_entry)
            je.voucher_type = 'Journal Entry'
            je.company = frappe.get_value("Global Defaults", None, "default_company")
            je.posting_date = self.bank_transaction.date
            je.cheque_date = self.bank_transaction.date
            je.cheque_no = advice['utr_number']
            je.submit()
            frappe.db.commit()

        except Exception as e:
            new_doc = frappe.new_doc('ToDo')
            new_doc.description = str(e)
            new_doc.save()
            print("Error:", e)

    def get_claim(self, claim_id):
        claims = frappe.db.sql("""
        SELECT * FROM `tabClaimBook` WHERE cl_number = %(claim_id)s
        """,values = { 'claim_id' : claim_id}, as_dict = 1)
        
        if len(claims) == 1:
            return claims[0]
        else:            
            frappe.throw("More than one claim")
           
    def get_sales_invoice(self, bill_number):
        sales_invoices = frappe.db.sql("""
        SELECT * FROM `tabSales Invoice` WHERE name = %(name)s  
        """,values = { 'name' : bill_number}, as_dict=1)

        if len(sales_invoices) == 1:
            return sales_invoices[0]
        else:
            frappe.throw("No Sales Invoice Found: " + str(bill_number))

        
    def create_payment_entry_item(self, advice):
    
        if(self.available_amount <= 0):
            return None

        invoice_number = 0

        if advice.bill_no:
            invoice_number = advice.bill_no
        else:
            claim = self.get_claim(advice.claim_id)
            if claim:
                invoice_number = claim.final_bill_number
        
        if invoice_number:
            sales_invoice = self.get_sales_invoice(invoice_number)
        else:
            return None

        if self.available_amount >= advice.settlement_amount:
            if advice.settlement_amount <= sales_invoice.outstanding_amount:
                allocated_amount = advice.settlement_amount
            else:
                frappe.throw("Settlement Amount should be less than the Outstanding Amount for " + str(invoice_number))
                
        else:
            allocated_amount = self.available_amount

        self.available_amount = self.available_amount - allocated_amount
        
        entry = {
            'account': 'Debtors - A',
            'party_type': 'Customer',
            'party': sales_invoice['customer'],
            'credit_in_account_currency': allocated_amount,
            'reference_type': 'Sales Invoice',
            'reference_name': sales_invoice.name,
            'reference_due_date': sales_invoice.posting_date,
            'region': sales_invoice.region
        }

        if advice.tds_amount:
            if advice.tds_amount > sales_invoice.outstanding_amount:
                return entry, None
            
            tds_entry = [
                {
                'account': 'Debtors - A',
                'party_type': 'Customer',
                'party': sales_invoice['customer'],
                'credit_in_account_currency': advice.tds_amount,
                'reference_type': 'Sales Invoice',
                'reference_name': sales_invoice.name,
                'reference_due_date': sales_invoice.posting_date,
                'user_remark': 'tds credits',
                'region': sales_invoice.region
              },
              {
                'account': 'TDS Credits - A',
                'party_type': 'Customer',
                'party': sales_invoice['customer'],
                'debit_in_account_currency': advice.tds_amount,
                'region': sales_invoice.region
                'user_remark': 'tds debits'
            }
            ]
            return entry, tds_entry
        return entry, None
    
        
def get_unreconciled_bank_transactions():
    return frappe.db.sql("""
    SELECT * FROM `tabBank Transaction` WHERE status in ('unreconciled', 'pending')""", as_dict=1)

@frappe.whitelist()
def create_payment_entries():
    bank_transactions = get_unreconciled_bank_transactions()
    for bank_transaction in bank_transactions:
        # print(bank_transaction.deposit)
        if bank_transaction.deposit and bank_transaction.deposit > 0:
            t = BankTransactionWrapper(bank_transaction)
            t.process()
