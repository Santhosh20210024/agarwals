import frappe
import traceback


class BankTransactionWrapper():
    
    def __init__(self, bank_transaction):
        self.bank_transaction = bank_transaction
        self.available_amount = bank_transaction.deposit
        self.advice_log = { "bnk.utr": None, "sa.utr": None, "sa.bill": None, "sa.claim": None, "cb.al": None, "cb.cl": None, "dbr.claim": None, "dbr.bill": None }
        self.advice_log_value = {  "sa.utr" : None, "cb.al": None, "cb.cl": None, "dbr.claim": None, "dbr.bill": None  }
    
    def clear_advice_log(self): # Clear the self.advice_log 
        for log in self.advice_log:
            self.advice_log[log] = None
            if log in self.advice_log_value.keys():
                self.advice_log_value[log] = None

    def add_log_entries(self, advice_name):
        advice_doc = frappe.get_doc("Settlement Advice", advice_name)
        
        # Verify whether the advice is already passed
        frappe.db.sql('DELETE FROM `tabMatch Log` WHERE parent = %(parent)s', values = { 'parent' : advice_name})
        frappe.db.commit()

        # Explicit handled the settlement advice direct matching ( bill no )
        if self.advice_log['sa.bill'] != None:
            if self.advice_log['sa.claim'] == None:
                if self.advice_log['dbr.bill'] != None:
                    log = { 'status': 'Pass', 
                            'log': f"> bnk.utr [{self.advice_log['bnk.utr']}] > sa.utr [{self.advice_log['sa.utr']}] > sa.bill [{self.advice_log['sa.bill']}] > dbr.bill [{self.advice_log['dbr.bill']}]"}
                    advice_doc.append('match_log', log)
                    advice_doc.save()
                    return
                
                else:
                    log = { 'status': 'Fail', 
                                    'log': f"> bnk.utr [{self.advice_log['bnk.utr']}] > sa.utr [{self.advice_log['sa.utr']}] > sa.bill [{self.advice_log['sa.bill']}] > dbr.bill"}
                    advice_doc.append('match_log', log)
        
        match_log = '' 
        for log in self.advice_log.keys():
            if log == 'sa.bill': # The sa.bill is already handled
                continue
            if log == 'dbr.claim' and self.advice_log[log] == None:
                continue
            if log == 'cb.cl' and self.advice_log['cb.al'] != None:
                continue
            else:
                if self.advice_log[log] != None:
                    match_log += f'> {log} [{self.advice_log[log]}] ' # For sucess addition
                else:
                    if log in self.advice_log_value.keys(): # Handling the failure cases
                        if self.advice_log_value[log] != None:
                            match_log += f'> {log} [{self.advice_log_value[log]}]'
                            
                            advice_doc.append('match_log', { 'status' : 'Fail', 'log': f"{match_log}" })
                        else:
                            advice_doc.append('match_log', { 'status' : 'Fail', 'log': f"{match_log} > {log}" })
                    else:
                        advice_doc.append('match_log', { 'status' : 'Fail', 'log': f"{match_log} > {log}" })
        
        if 'dbr.bill' in match_log and self.advice_log['dbr.bill'] != None: 
            advice_doc.append('match_log', { 'status': 'Success', 'log': match_log })

        advice_doc.save()

    def sales_utr_entry(self, tds_je_ac, bank_je_ac):
        bank_invoice_list = [je.reference_name for je in bank_je_ac if je.account == 'Debtors - A']
        tds_invoice_list = [je.reference_name for je in tds_je_ac if je.account == 'Debtors - A']
        invoice_list = bank_invoice_list + tds_invoice_list

        for invoice in set(invoice_list):
            sales_doc = frappe.get_doc('Sales Invoice', invoice)
            sales_doc.append("custom_utr_number", {
                "reference_number": self.bank_transaction.reference_number,
                "parenttype": 'Sales Invoice',
                "parent": sales_doc.name
            })
            sales_doc.save()
        frappe.db.commit()

    def process(self):
        try:
            self.bank_account = frappe.db.get_value('Bank Account', self.bank_transaction.bank_account, 'account')

            if self.bank_account == None:
                self.error_log(user_error_msg = f'Not able to find the bank account for this transaction { self.bank_transaction.reference_number }')
                frappe.db.commit()
                return 
            
            bnk_ref_num = str(self.bank_transaction.reference_number).strip().lstrip('0')

            # two way check in advice's utr - system generated UTR and original UTR
            advices  = frappe.db.sql("""
                       SELECT * FROM `tabSettlement Advice` WHERE final_utr_number = %(final_utr_number)s 
                       """, values = { 'final_utr_number' : bnk_ref_num }, 
                       as_dict = 1 )
            
            advices_org_utr = frappe.db.sql("""
                               SELECT * from `tabSettlement Advice` where TRIM(TRIM(LEADING '0' FROM utr_number)) = %(utr_number)s
                               """, values = { 'utr_number' : bnk_ref_num },
                               as_dict = 1)
            
            # need to verify, if it is necessary
            # advices = [item for item in advices if (item.status == None) or (item.status == 'Error' and item.retry == 1) ]
            
            org_flag = False
            if len(advices) == 0:
                if len(advices_org_utr) > 0:
                    advices = advices_org_utr
                    org_flag = True
            
            # advice intial validation
            if len(advices) < 1:
                self.error_log(user_error_msg= 'No Advices Found for the ' + str(self.bank_transaction.name))
                frappe.db.commit()
                return 
            
            bank_je = frappe.new_doc('Journal Entry')
            tds_je = frappe.new_doc('Journal Entry')
            bank_je.accounts = []

            # created for settlement advice reference field in JE
            bank_je_advices = []
            tds_je_advices = []

            for advice in advices:
                self.clear_advice_log()

                if advice.status == 'Error': # clear the existing logs
                    frappe.db.set_value( 'Settlement Advice', advice.name, 'status', '')
                    frappe.db.set_value( 'Settlement Advice', advice.name, 'remark', '')
                    frappe.db.commit()

                if not (advice.claim_id or advice.bill_no):
                    continue

                if self.available_amount <= 0:
                    break
                
                self.advice_log["bnk.utr"] = self.bank_transaction.reference_number # bank utr

                if org_flag == True: # only for log value
                    self.advice_log["sa.utr"] = advice['utr_number']
                else:
                    self.advice_log["sa.utr"] = advice['final_utr_number']
                
                entry, tds_entry = self.create_payment_entry_item(advice)
                self.add_log_entries(advice.name) # Need to verify
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
                bank_je.custom_bank_reference = self.bank_transaction.reference_number
                bank_je.name = self.bank_transaction.reference_number
                bank_je = self.get_advice_obj_list(bank_je_advices, bank_je)
                bank_je.submit()
                self.set_transaction_reference(bank_je.name, allocated_amount)
            
            if tds_je.accounts != None and len(tds_je.accounts) > 0:
                self.create_tds_entries(tds_je,tds_je_advices)
            if len(tds_je.accounts) > 0 or len(bank_je.accounts) > 0:
                # need to change the status
                self.sales_utr_entry(tds_je.accounts, bank_je.accounts)
                
                for advice in set(bank_je_advices  +  tds_je_advices):
                    frappe.set_value('Settlement Advice', advice, 'status', 'Processed')
                frappe.db.commit()

        except Exception as error:
            self.error_log(system_error_msg = error, bank_utr = self.bank_transaction.reference_number)
            
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
        claim_flag = ''

        # By default Check the claim bill no
        bill_claim = frappe.db.sql("""
                       SELECT name as custom_raw_bill_number, claim_id FROM `tabBill` WHERE claim_id = %(claim_id)s
                        """, values = { 'claim_id' : claim_id }
                        , as_dict = 1)
    
        claims_al = frappe.db.sql("""
                    SELECT * FROM `tabClaimBook` WHERE al_number = %(claim_id)s
                    """, values = { 'claim_id' : claim_id }
                    , as_dict = 1)
        
        claims_cl = frappe.db.sql("""
                        SELECT * FROM `tabClaimBook` WHERE cl_number = %(claim_id)s
                        """, values = {'claim_id' : claim_id}
                        , as_dict = 1)
        
        if len(claims_al) > 0:
            if(len(claims_al) > 1): 
                self.advice_log_value['cb.al'] = "More than one claim based on al_number"

            else:
                if len(bill_claim) > 0:
                    if len(bill_claim) == 1:
                        if claims_al[0]['custom_raw_bill_number'] == bill_claim[0]['custom_raw_bill_number']:
                            self.advice_log['cb.al'] = claims_al[0]['al_number']
                            return claims_al
                        else:
                            # need to put the remarks
                            self.advice_log['cb.al'] = claims_al[0]['al_number'] + '( Valid al, Mismatched bill no )'
                            return bill_claim
                    else:
                        self.advice_log['cb.al'] = claims_al[0]['al_number']
                        return claims_al
                else:
                    self.advice_log['cb.al'] = claims_al[0]['al_number']
                    return claims_al
            if len(claims_al) == 1:
                self.advice_log_value['cb.al'] = claims_al[0]['al_number'] # [cb.al] advice log reference
        
        elif len(claims_cl) > 0:
            if(len(claims_cl) > 1):
                self.advice_log_value['cb.cl'] = "More than one claim based on cl_number"
            else:
                if len(bill_claim) > 0:
                    if len(bill_claim) == 1:
                        if claims_cl[0]['custom_raw_bill_number'] == bill_claim[0]['custom_raw_bill_number']:
                            self.advice_log['cb.cl'] = claims_cl[0]['cl_number']
                            return claims_cl
                        else:
                            # need to put the remarks
                            self.advice_log['cb.cl'] = claims_cl[0]['cl_number'] + '( Valid cl, Mismatched bill no )'
                            return bill_claim
                    else:
                        self.advice_log['cb.cl'] = claims_cl[0]['cl_number']
                        return claims_cl
                else:
                    self.advice_log['cb.cl'] = claims_cl[0]['cl_number']
                    return claims_cl
            if len(claims_al) == 1:
                self.advice_log_value['cb.cl'] = claims_al[0]['cl_number']

        elif len(bill_claim) > 0:
            if len(bill_claim) > 1:
               self.advice_log_value['dbr.claim'] = "More than one bill based on claim number"
            else:
                self.advice_log['dbr.claim'] = bill_claim[0]['claim_id']
                return bill_claim
            
        elif len(claim_flag) > 0:
            self.error_log(advice, user_error_msg = f"{claim_flag} - { str(claim_id) }" )
            return None
         
        else:
            self.error_log(advice, user_error_msg = f"No claim exists: {str(claim_id)}" )
            return None
        
    # Refactored
    def get_sales_invoice(self, advice, bill_number):

        sales_invoices = frappe.db.sql("""
                         SELECT * FROM `tabSales Invoice` WHERE name = %(name)s and status != 'Cancelled'
                         """, values = { 'name' : bill_number}, as_dict=1)

        if len(sales_invoices) == 1: #extra validation
            return sales_invoices[0]
        
        else:
            self.error_log(advice, user_error_msg = f"No Sales Invoice Found: {str(bill_number)}")
            return None
        
    def create_payment_entry_item(self, advice):
    
        if(self.available_amount <= 0):
            return None,None
        
        invoice_number = 0

        if advice.bill_no:
            invoice_number = advice.bill_no
            self.advice_log['sa.bill'] = advice.bill_no
            if len(frappe.get_all('Bill',filters={'name':advice.bill_no},fields=['name'])) == 0:
                claim = self.get_claim(advice, advice.claim_id)

                if claim != None:
                    if len(claim) > 0:
                        self.advice_log['sa.claim'] = advice.claim_id
                        invoice_number = claim[0].custom_raw_bill_number
                else:
                    self.advice_log_value['sa.claim'] = advice.claim_id
        else:
            claim = self.get_claim(advice, advice.claim_id)

            if claim != None:
                if len(claim) > 0:
                    self.advice_log['sa.claim'] = advice.claim_id
                    invoice_number = claim[0].custom_raw_bill_number
            else:
                self.advice_log_value['sa.claim'] = advice.claim_id
        
        if invoice_number:
            sales_invoice = self.get_sales_invoice(advice, invoice_number)
            if sales_invoice  != None:
                self.advice_log['dbr.bill'] = sales_invoice.name
            if sales_invoice == None:
                return None,None
        else:
            return None,None
        
        if self.available_amount >= advice.settled_amount:
            if advice.settled_amount <= sales_invoice.outstanding_amount:
                allocated_amount = advice.settled_amount
            else:
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
            'cost_center': sales_invoice.cost_center,
            'branch_type': sales_invoice.branch_type
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
                'cost_center': sales_invoice.cost_center,
                'branch_type': sales_invoice.branch_type
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
                'cost_center': sales_invoice.cost_center,
                'branch_type': sales_invoice.branch_type
            }
            ]
            return entry, tds_entry
        return entry, None
    
    def error_log(self,advice = None, system_error_msg = None, user_error_msg = None, bank_utr = None):
        error_record_doc = frappe.new_doc('Error Record Log')
        error_record_doc.doctype_name = "Journal Entry"
        
        if advice != None: # also populate the error case in settlement advices
            advice_doc = frappe.get_doc('Settlement Advice', advice.name)
            advice_doc.status = 'Error'
            if not user_error_msg:
                if bank_utr != None:
                    advice_doc.remark = f"Error: {str(system_error_msg)} : {bank_utr}"
                else:
                    advice_doc.remark = f"Error: {str(system_error_msg)}"
                advice_doc.save()
            else:
                if bank_utr != None: 
                    advice_doc.remark = user_error_msg + " : " + bank_utr
                else:
                    advice_doc.remark = user_error_msg
                advice_doc.save()
        
        if not user_error_msg:
            trace_info = traceback.format_exc()
            if bank_utr != None:
                error_record_doc.error_message = f"Error: {str(system_error_msg)}\n\nTraceback:\n{trace_info} : {bank_utr}"
            else:
                error_record_doc.error_message = f"Error: {str(system_error_msg)}\n\nTraceback:\n{trace_info}"
            error_record_doc.save()
        else:
            if bank_utr != None:
                error_record_doc.error_message = user_error_msg + " : " + bank_utr
            else:
                error_record_doc.error_message = user_error_msg

            error_record_doc.save()

def payment_batch_operation(chunk):
    for record in chunk:
        transaction_doc = frappe.get_doc("Bank Transaction", record)
        transaction = BankTransactionWrapper(transaction_doc)
        transaction.process()
        
def get_unreconciled_bank_transactions():
    return frappe.db.sql("""
    SELECT name FROM `tabBank Transaction` WHERE status in ('unreconciled', 'pending') AND deposit > 0 AND deposit is NOT NULL AND LENGTH(reference_number) > 1 AND reference_number != '0' AND unallocated_amount > 10""", as_dict=1)

@frappe.whitelist()
def create_payment_entries():
    unreconciled_bank_transactions = get_unreconciled_bank_transactions()
    pending_transactions = []

    for bank_transaction in unreconciled_bank_transactions:
            pending_transactions.append(bank_transaction.name)

    chunk_size = 1000
    for i in range(0, len(pending_transactions), chunk_size):
        frappe.enqueue( payment_batch_operation, queue='long', is_async=True, timeout=18000, chunk = pending_transactions[i:i + chunk_size] )
