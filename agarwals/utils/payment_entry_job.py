import frappe
import traceback


class BankTransactionWrapper():
    
    def __init__(self, bank_transaction):
        self.bank_transaction = bank_transaction
        self.available_amount = bank_transaction.deposit
        self.advice_log = { "bnk.utr": None, "sa.bill":None, "sa.claim": None, "cb.al": None, "cb.cl": None, "dbr.claim": None, "dbr.bill": None }

    def clear_advice_log(self): # TESTED
        # Clear the self.advice_log 
        for log in self.advice_log:
            self.advice_log[log] = None

    def add_log_entries(self, advice_name):
        advice_doc = frappe.get_doc("Settlement Advice", advice_name)
        
        is_advice_pass = frappe.get_list("Match Log", filters={ 'parent' : advice_name, 'status': 'Pass' }) # tested
        if len(is_advice_pass) > 0: # Tested
            return 

        # Explicit check for the advice direct matching bill no
        if self.advice_log['sa.bill'] != None: # tested
            if self.advice_log['dbr.bill'] != None: # tested
                _log = { 'status': 'Pass', 
                         'log': f"> bnk.utr [{self.advice_log['bnk.utr']}] > sa.bill [{self.advice_log['sa.bill']}] > dbr.bill [{self.advice_log['dbr.bill']}]"}
                
                advice_doc.append('match_log', _log)
                advice_doc.save()
                return
            else:
                _log = { 'status': 'Fail', 
                                   'log': f"> bnk.utr [{self.advice_log['bnk.utr']}] > dbr.bill [{self.advice_log['dbr.bill']}]"}
                advice_doc.append('match_log', self.add_entry('Fail','sa.bill'))
        
        _advices_log = '' 
        for log in self.advice_log.keys():
            if log == 'sa.bill': #t
                continue
            if log == 'dbr.claim' and self.advice_log[log] == None: #t
                continue
            else:
                if self.advice_log[log] != None: #t
                    _advices_log += f'> {log} [{self.advice_log[log]}] '
                else: #t #need to add number
                    advice_doc.append('match_log', { 'status' : 'Fail', 'log': f"{_advices_log} > {log}" })
        
        if 'dbr.bill' in _advices_log: 
            advice_doc.append('match_log', { 'status': 'Success', 'log': _advices_log })

        advice_doc.save()

    def process(self):
        try:
            self.bank_account = frappe.db.get_value('Bank Account', self.bank_transaction.bank_account, 'account')
            
            advices  = frappe.db.sql("""
                SELECT * FROM `tabSettlement Advice` WHERE utr_number = %(utr_number)s
                """, values = { 'utr_number' : str(self.bank_transaction.reference_number).strip().lstrip('0') }, as_dict = 1 )
            
            # Need to check
            # advices = [item for item in advices if (item.status == None) or (item.status == 'Error' and item.retry == 1) ]
            
            # advices validation
            if len(advices) < 1:
                self.error_log(user_error_msg= 'No Advices Found for the ' + str(self.bank_transaction.name))
                frappe.db.commit()
                return # tested
            
            bank_je = frappe.new_doc('Journal Entry')
            tds_je = frappe.new_doc('Journal Entry')
            bank_je.accounts = []
            bank_je_advices = []
            tds_je_advices = []

            for advice in advices:
                self.clear_advice_log() # tested

                if advice.status == 'Error':
                    frappe.db.set_value( 'Settlement Advice', advice.name, 'status', '')
                    frappe.db.set_value( 'Settlement Advice', advice.name, 'remark', '')
                    frappe.db.commit()

                if not (advice.claim_id or advice.bill_no): # tested
                    continue

                if self.available_amount <= 0: # tested
                    break
                
                self.advice_log["bnk.utr"] = self.bank_transaction.reference_number # tested
                entry, tds_entry = self.create_payment_entry_item(advice) # tested for payment ( 1. sa.bill no - > dbr.bill_no entry and tds)
                self.add_log_entries(advice.name) # NEED TO ASK
                frappe.db.commit()

                if entry:
                    bank_je.append('accounts', entry)
                    bank_je_advices.append(advice.name)
                    if tds_entry:
                        tds_je.append('accounts', tds_entry[0])
                        tds_je.append('accounts', tds_entry[1])
                        tds_je_advices.append(advice.name)
                else:
                    continue
            if  bank_je.accounts != None and len(bank_je.accounts) > 0:
                allocated_amount = self.bank_transaction.deposit - self.available_amount
                asset_entry = {'account': self.bank_account, 'debit_in_account_currency': allocated_amount }
                bank_je.append('accounts', asset_entry)
                bank_je.voucher_type = 'Bank Entry'
                bank_je.company = frappe.get_value("Global Defaults", None, "default_company")
                bank_je.posting_date = self.bank_transaction.date
                bank_je.cheque_date = self.bank_transaction.date
                bank_je.cheque_no = self.bank_transaction.name
                bank_je.custom_bank_reference = self.bank_transaction.reference_number # tested
                bank_je.name = self.bank_transaction.reference_number
                bank_je = self.get_advice_obj_list(bank_je_advices, bank_je) # need to test
                bank_je.submit()
                self.set_transaction_reference(bank_je.name, allocated_amount)
            
            if tds_je.accounts != None and len(tds_je.accounts) > 0:
                self.create_tds_entries(tds_je,tds_je_advices) #need to test
            if len(tds_je.accounts) > 0 or len(bank_je.accounts) > 0:
                # need to change the status
                frappe.db.commit()
        except Exception as error:
            self.error_log(system_error_msg = error)
            
    def get_advice_obj_list(self, advices, je_doc):
        for advice in advices:
            je_doc.append("custom_settlement_advice_reference", {
                "advices": advice,
                "parenttype": 'Journal Entry',
                "parent": je_doc.name
            })
        return je_doc
    
    def create_tds_entries(self, tds_je, tds_je_advices):
        try:
            name_ref = self.bank_transaction.reference_number or self.bank_transaction.name
            tds_je.name = str(name_ref) + "-" + "TDS"
            tds_je.voucher_type = 'Credit Note'
            tds_je.company = frappe.get_value("Global Defaults", None, "default_company")
            tds_je.posting_date = self.bank_transaction.date
            tds_je.cheque_date = self.bank_transaction.date
            tds_je = self.get_advice_obj_list(tds_je_advices, tds_je)
            tds_je.cheque_no = str(name_ref)
            tds_je.submit()
        except Exception as e:
            self.error_log(user_error_msg='Error acquired during tds entry creation bank_reference =' + str(self.bank_transaction.name))
            return 
        
    def set_transaction_reference(self, je_name, allocated_amount):
        payment_entries = [{
            'payment_document': 'Journal Entry',
            'payment_entry': je_name,
            'allocated_amount': allocated_amount
        }]
        corres_bank_transaction = frappe.get_doc('Bank Transaction', self.bank_transaction.name)
        corres_bank_transaction.set('payment_entries', payment_entries)
        corres_bank_transaction.submit()
        
    # Checking on both al_number and cl_number
    def get_claim(self, advice, claim_id):
        _flag = ''
        
        # By default Check the claim bill no
        bill_claimId = frappe.db.sql("""
                       SELECT name as custom_raw_bill_number,claim_id FROM `tabBill` WHERE claim_id = %(claim_id)s
                        """, values = { 'claim_id' : claim_id }, as_dict = 1) # tested
    
        claims_al = frappe.db.sql("""
                    SELECT * FROM `tabClaimBook` WHERE al_number = %(claim_id)s
                    """, values = { 'claim_id' : claim_id }, as_dict = 1) # testd

        claims_cl = frappe.db.sql("""
                    SELECT * FROM `tabClaimBook` WHERE cl_number = %(claim_id)s
                    """, values = {'claim_id' : claim_id}, as_dict = 1) # tested
        
        if len(claims_al) > 0: #t
            if(len(claims_al) > 1): 
                _flag += "More than one claim based on al_number"

            else:
                if len(bill_claimId) > 0:
                    if claims_al[0]['custom_raw_bill_number'] == bill_claimId[0]['custom_raw_bill_number']:
                        self.advice_log['cb.al'] = claims_al[0]['custom_raw_bill_number']
                        return claims_al
                    else:
                        # need to put the remarks
                        self.advice_log['cb.al'] = claims_al[0]['custom_raw_bill_number'] + '( Valid al, Mismatched bill no )'
                        return bill_claimId
                else:
                    return claims_al
                
        elif len(claims_cl) > 0: #t
            if(claims_cl) > 0:
                if(len(claims_cl) > 1):
                    _flag += ",More than one claim based on cl_number"
                else:
                    if len(bill_claimId) > 0:
                        if claims_cl['custom_raw_bill_number'] == bill_claimId['custom_raw_bill_number']:
                            self.advice_log['cb.cl'] = claims_cl
                            return claims_cl
                        else:
                            # need to put the remarks
                            self.advice_log['cb.cl'] = claims_cl + '( Valid cl, Mismatched bill no )'
                            return bill_claimId
                    else:
                        return claims_cl
                    
        elif len(bill_claimId) > 0: #tested
            if len(bill_claimId) > 1:
               _flag += ",More than one bill based on claim number"
            else:
                self.advice_log['dbr.claim'] = bill_claimId[0].claim_id
                return bill_claimId
            
        elif len(_flag) > 0:
            self.error_log(advice, user_error_msg = _flag + str(claim_id))
            return None
         
        else:
            self.error_log(advice, user_error_msg = "No claim exists: " + str(claim_id) )
            return None
        
    # Refactored
    def get_sales_invoice(self, advice, bill_number):

        sales_invoices = frappe.db.sql("""
        SELECT * FROM `tabSales Invoice` WHERE name = %(name)s
        """, values = { 'name' : bill_number}, as_dict=1)

        if len(sales_invoices) == 1:
            return sales_invoices[0]
        
        else:
            self.error_log(advice, user_error_msg="No Sales Invoice Found: " + str(bill_number))
            return None
        
    def create_payment_entry_item(self, advice):
    
        if(self.available_amount <= 0):
            return None,None
        
        invoice_number = 0

        if advice.bill_no: # TESTED
            invoice_number = advice.bill_no
            self.advice_log['sa.bill'] = advice.bill_no
        else:
            self.advice_log['sa.claim'] = advice.claim_id
            claim = self.get_claim(advice, advice.claim_id)
            if len(claim) > 0: #t
                invoice_number = claim[0].custom_raw_bill_number
        
        if invoice_number: # tested
            sales_invoice = self.get_sales_invoice(advice, invoice_number)
            self.advice_log['dbr.bill'] = sales_invoice.name
            if sales_invoice == None: # tested
                return None,None
        else:
            return None,None
        
        if self.available_amount >= advice.settled_amount:
            if advice.settled_amount <= sales_invoice.outstanding_amount:
                allocated_amount = advice.settled_amount
            else: # TESTED
                self.error_log(advice, user_error_msg = "Settlement Amount is greater than the Outstanding Amount for " + str(invoice_number))
                return None,None
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
            'region': sales_invoice.region,
            'entity': sales_invoice.entity,
            'branch': sales_invoice.branch.split("-")[0],
            'cost_center': sales_invoice.cost_center
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
                'region': sales_invoice.region,
                'entity': sales_invoice.entity,
                'branch': sales_invoice.branch.split("-")[0],
                'cost_center': sales_invoice.cost_center
              },
              {
                'account': 'TDS Credits - A',
                'party_type': 'Customer',
                'party': sales_invoice['customer'],
                'debit_in_account_currency': advice.tds_amount,
                'region': sales_invoice.region,
                'user_remark': 'tds debits',
                'region': sales_invoice.region,
                'entity': sales_invoice.entity,
                'branch': sales_invoice.branch.split("-")[0],
                'cost_center': sales_invoice.cost_center
            }
            ]
            return entry, tds_entry
        return entry, None
    
    def error_log(self,advice = None, system_error_msg = None, user_error_msg = None):
        error_record_doc = frappe.new_doc('Error Record Log')
        error_record_doc.doctype_name = "Journal Entry"
        
        if advice != None:
            advice_doc = frappe.get_doc('Settlement Advice', advice.name)
            advice_doc.status = 'Error'
            if not user_error_msg:
                advice_doc.remark = f"Error: {str(system_error_msg)}"
                advice_doc.save()
            else:
                advice_doc.remark = user_error_msg
                advice_doc.save()
        
        if not user_error_msg:
            trace_info = traceback.format_exc()
            error_record_doc.error_message = f"Error: {str(system_error_msg)}\n\nTraceback:\n{trace_info}"
            error_record_doc.save()
        else:
            error_record_doc.error_message = user_error_msg
            error_record_doc.save()

def payment_batch_operation(chunk):
    for record in chunk:
        transaction_doc = frappe.get_doc("Bank Transaction", record)
        transaction = BankTransactionWrapper(transaction_doc)
        transaction.process()
        
def get_unreconciled_bank_transactions(): # tested
    return frappe.db.sql("""
    SELECT * FROM `tabBank Transaction` WHERE status in ('unreconciled', 'pending') AND deposit > 0 AND deposit is NOT NULL AND LENGTH(reference_number) > 1 AND unallocated_amount > 10;""", as_dict=1)

@frappe.whitelist()
def create_payment_entries():
    unreconciled_bank_transactions = get_unreconciled_bank_transactions()
    bank_transactions = []

    for bank_transaction in unreconciled_bank_transactions: # tested
            # transaction_doc = frappe.get_doc("Bank Transaction", record)
            transaction = BankTransactionWrapper(bank_transaction)
            transaction.process()
            bank_transactions.append(bank_transaction.name)
            
    chunk_size = 1000
    for i in range(0, len(bank_transactions), chunk_size):
        frappe.enqueue( payment_batch_operation, queue='long', is_async=True, timeout=18000, chunk = bank_transactions[i:i + chunk_size] )