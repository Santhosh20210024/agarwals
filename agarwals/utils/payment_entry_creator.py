import frappe
from frappe.utils.caching import redis_cache
from frappe import utils
from datetime import date
 
class PaymentEntryCreator:
    """ For Reconcilation Process """
    
    def add_log_error(self, doctype, record_name = None, error_msg = None):
        error_log_record = frappe.new_doc('Payment Entry Error Log')
        error_log_record.set('reference_doctype',doctype)
       
        if record_name:
            error_log_record.set('reference_record',record_name)
        error_log_record.set('error_message',error_msg)
        error_log_record.save()
 
    def update_trans_reference(self, bt_doc, pe_doc):
        bt_doc = frappe.get_doc('Bank Transaction', bt_doc.name)
        bt_doc.append('payment_entries',
                      {'payment_document': 'Payment Entry'
                      ,'payment_entry': pe_doc.name
                      ,'allocated_amount': pe_doc.paid_amount})
        bt_doc.submit()

    def process_rounding_off(self, pe_doc, si_doc): 
        deductions = []
        si_outstanding_amount = frappe.get_value('Sales Invoice', si_doc.name, 'outstanding_amount')
        si_allocated_amount = pe_doc.references[0].allocated_amount
        si_outstanding_amount = round(float(si_outstanding_amount - si_allocated_amount),2)
 
        if si_outstanding_amount <= 9.9 and si_outstanding_amount != 0.00:
            deductions.append(self.add_deduction('Write Off - A', si_doc, 'WriteOff', round(float(si_outstanding_amount),2)))
 
        if deductions:
            pe_doc.references[0].allocated_amount = round(float(pe_doc.references[0].allocated_amount),2) + round(float(si_outstanding_amount),2)
            deductions = pe_doc.deductions + deductions
            pe_doc.set("deductions", deductions)
        
        return pe_doc
   
    def add_deduction(self, account, si_doc, description, amount):
        return {'account': account, 'cost_center': si_doc.cost_center,
                'description': description, 'branch': si_doc.branch,
                'entity': si_doc.entity,'region': si_doc.region,
                'branch_type': si_doc.branch_type, 'amount': amount}
    
    def create_payment_entry(self, name, si_doc,  bank_account, bt_doc, settled_amount):
        pe_doc = frappe.new_doc('Payment Entry')
        pe_doc.set('name',name)
        pe_doc.set('custom_sales_invoice', si_doc.name)
        pe_doc.set('payment_type', 'Receive')
        pe_doc.set('mode_of_payment', 'Bank Draft')
        pe_doc.set('party_type', 'Customer')
        pe_doc.set('party', si_doc.customer)
        pe_doc.set('bank_account', bt_doc.bank_account)
        pe_doc.set('paid_to', bank_account)
        pe_doc.set('paid_from', 'Debtors - A')
        pe_doc.set('paid_amount', settled_amount)
        pe_doc.set('received_amount', settled_amount)
        pe_doc.set('reference_no', bt_doc.reference_number)
        pe_doc.set('reference_date', bt_doc.date)
        pe_doc.set('cost_center', si_doc.cost_center)
        pe_doc.set('branch', si_doc.branch)
        pe_doc.set('entity', si_doc.entity)
        pe_doc.set('region', si_doc.region)
        pe_doc.set('branch_type', si_doc.branch_type)
        pe_doc.set('custom_due_date', si_doc.posting_date)
        return pe_doc
    
    def get_entry_name(self, si_doc):
        existing_payment_entries = frappe.get_list('Payment Entry'
                                   ,filters={'custom_sales_invoice':si_doc.name})
       
        if existing_payment_entries:
            name = si_doc.name + "-" + str(len(existing_payment_entries))
        else:
            name = si_doc.name
        
        return name
   
    def get_posting_date(self, bt_doc): # Need to test
        closing_date_list = frappe.get_list('Period Closer by Entity',
                                            filters={'entity': bt_doc.custom_entity}
                                            ,order_by = 'creation desc'
                                            ,pluck = 'posting_date')  

        if closing_date_list:
            closing_date = max(closing_date_list)
            if bt_doc.date < closing_date:
                return utils.today()
        else:
            return bt_doc.date

    def process_payment_entry(self
                              ,bt_doc
                              ,si_doc
                              ,bank_account
                              ,settled_amount
                              ,tds_amount = 0
                              ,disallowed_amount = 0):
        try:
            deductions = []
            name = self.get_entry_name(si_doc = si_doc)
            pe_doc = self.create_payment_entry(name
                                               ,si_doc
                                               ,bank_account
                                               ,bt_doc
                                               ,settled_amount)
            
            pe_doc.set('posting_date', self.get_posting_date(bt_doc))
            reference_item = [{
                'reference_doctype': 'Sales Invoice',
                'reference_name': si_doc.name,
                'allocated_amount': settled_amount + tds_amount + disallowed_amount
            }]
            pe_doc.set('references', reference_item) 

            if tds_amount > 0:
                deductions.append(self.add_deduction('TDS - A', si_doc, 'TDS', tds_amount))
                pe_doc.set('custom_tds_amount', tds_amount)
 
            if disallowed_amount > 0:
                deductions.append(self.add_deduction('Disallowance - A', si_doc, 'Disallowance', disallowed_amount))
                pe_doc.set('custom_disallowed_amount', disallowed_amount)
 
            if deductions:
                pe_doc.set('deductions', deductions)

            pe_doc = self.process_rounding_off(pe_doc, si_doc)
            pe_doc.save()
            pe_doc.submit()
            frappe.db.commit()
            
            self.update_trans_reference(bt_doc, pe_doc)
            frappe.db.commit()
            return pe_doc
       
        except Exception as err:
            self.add_log_error('Payment Entry', si_doc.name, error_msg = err)
            return ''
 
    def get_document_record(self, doctype, name): 
        return frappe.get_doc(doctype,name)
    
    def update_matcher_log(self, name, status, msg):
        frappe.set_value('Matcher', name, 'status', status)
        frappe.set_value('Matcher', name, 'remarks', msg)
 
    @redis_cache
    def get_company_account(self, bank_account_name):
        bank_account = frappe.get_doc('Bank Account', bank_account_name)
        if not bank_account.account:
            return None
        return bank_account.account
   
    def update_invoice_reference(self, si_doc, payment_entry, record): 
        si_doc = self.get_document_record('Sales Invoice', si_doc)
        bt_doc = frappe.get_list("Bank Transaction", filters={'name': payment_entry.reference_no}, fields=['bank_account', 'custom_region', 'custom_entity'])
        created_date = date.today().strftime("%Y-%m-%d")
    
        si_doc.append('custom_reference', {'entry_type': 'Payment Entry', 'entry_name': payment_entry.name, 
                                           'paid_amount': payment_entry.paid_amount,'tds_amount': payment_entry.custom_tds_amount,
                                           'disallowance_amount': payment_entry.custom_disallowed_amount,'allocated_amount': payment_entry.total_allocated_amount,
                                           'utr_number': payment_entry.reference_no, 'utr_date': payment_entry.reference_date,
                                           'created_date': created_date, 'bank_region': bt_doc[0].custom_region,'bank_entity': bt_doc[0].custom_entity,
                                           'bank_account_number': payment_entry.bank_account })
        if record.settlement_advice:
            si_doc.append('custom_matcher_reference', {'id' : record.name, 'match_logic' : record.match_logic, 'settlement_advice': record.settlement_advice})
        else:
            if record.claim_book:
                si_doc.append('custom_matcher_reference', {'id' : record.name, 'match_logic' : record.match_logic, 'claim_book': record.claim_book})

        frappe.db.set_value('Matcher', record.name, 'status', 'Processed')
        si_doc.save()
        frappe.db.commit()
 
    def process(self, bt_doc_records, match_logic):
        """Process: Create payment entry based on the matcher logic ( MA1-CN, MA3-CN, MA5-BN ) only
           param1: bt_doc_records, 
           param2: match_logic,
           Return: None
        """

        if not len(bt_doc_records): 
            return
 
        for transaction_record in bt_doc_records: 
            if not transaction_record['date']:
                self.add_log_error('Bank Transaction', transaction_record['name'], "Date is Null")
                continue
 
            bank_account = self.get_company_account(transaction_record['bank_account'])
            if not bank_account:
                self.add_log_error('Bank Transaction', transaction_record['name'], "No Company Account Found")
                continue
 
            # Ordered By Payment Order
            # Amount Wise Descending Order
            matcher_records = frappe.db.sql("""
                          SELECT * from `tabMatcher`
                          where match_logic in %(logic)s
                          AND bank_transaction = %(reference_number)s
                          AND status = 'Open' 
                          order by payment_order ASC, tds_amount DESC , disallowance_amount DESC"""
                          ,values = {'reference_number' : transaction_record.name, 'logic': match_logic}
                          ,as_dict = True) 
 
            if matcher_records: 
                frappe.db.set_value('Bank Transaction', transaction_record['name'], 'custom_advice_status', 'Found')
 
            for record in matcher_records:
                try:
                    
                    bank_amount = 0 
                    settled_amount = round(float(record.settled_amount),2) if record.settled_amount else 0 
                    tds_amount = round(float(record.tds_amount),2) if record.tds_amount else 0 
                    disallowance_amount = round(float(record.disallowance_amount),2) if record.disallowance_amount else 0 
                    
                    if float(settled_amount) < 0 or float(tds_amount) < 0 or float(disallowance_amount) < 0:
                        self.update_matcher_log(record.name, 'Error', 'Amount Should Not Be Negative')
                        continue
                    
                    unallocated_amount = self.get_document_record('Bank Transaction', record.bank_transaction).unallocated_amount 
                    if frappe.db.get_value('Bank Transaction', record.bank_transaction, 'status') == 'Reconciled': # Already Reconciled
                        self.update_matcher_log(record.name, 'Error', 'Already Reconciled')
                        continue
                    
                    if not record.settled_amount: 
                        self.update_matcher_log(record.name, 'Error', 'Settled Amount Should Not Be Zero')
                        continue

                    si_doc = self.get_document_record('Sales Invoice', record.sales_invoice)
                    
                    if si_doc.total < (settled_amount + tds_amount + disallowance_amount):
                        self.update_matcher_log(record.name, 'Error', 'Claim amount lesser than the cumulative of other amounts')
                        continue
                
                    if si_doc.status == 'Paid': 
                        self.update_matcher_log(record.name, 'Error', 'Already Paid Bill')
                        continue

                    if si_doc.status == 'Cancelled': 
                        self.update_matcher_log(record.name, 'Error', 'Cancelled Bill')
                        continue

               
                    if record.settlement_advice: 
                        settlement_advice = self.get_document_record('Settlement Advice', record.settlement_advice)
                        settlement_advice.set('tpa', si_doc.customer)
                        settlement_advice.set('region', si_doc.region)
                        settlement_advice.set('entity', si_doc.entity)
                        settlement_advice.set('branch_type', si_doc.branch_type)
 
                    if settled_amount > unallocated_amount:
                        settled_amount = unallocated_amount
                        bank_amount = unallocated_amount

                    # Updating the corresponding fields in settlement advice and claimbook
                    if record.claimbook:
                        if record.settlement_advice:
                            settlement_advice.set('insurance_company_name', record.insurance_company_name)
                            settlement_advice.set('matched_bank_transaction', transaction_record['name'])
                            settlement_advice.set('matched_claimbook_record', record.claimbook)
                            settlement_advice.set('matched_bill_record', record.si_doc)
                        frappe.db.set_value('ClaimBook', record.claimbook, 'matched_status', 'Matched')
                        frappe.db.set_value('Sales Invoice', si_doc.name, 'custom_insurance_name', record.insurance_company_name)
                    else:
                        if record.settlement_advice:
                            settlement_advice.set('matched_bank_transaction', transaction_record['name'])
                            settlement_advice.set('matched_bill_record',record.si_doc)
 
                    if si_doc.outstanding_amount < settled_amount:
                        settled_amount = si_doc.outstanding_amount
 
                    if si_doc.outstanding_amount < settled_amount + tds_amount + disallowance_amount:
                       
                        if si_doc.outstanding_amount >= settled_amount + tds_amount:
                            payment_entry = self.process_payment_entry(
                                                transaction_record
                                                ,si_doc
                                                ,bank_account
                                                ,settled_amount
                                                ,tds_amount)
                           
                            if record.settlement_advice:
                                settlement_advice.set('remark', 'Disallowance amount is greater than Outstanding Amount')
                       
                        elif si_doc.outstanding_amount >= settled_amount + disallowance_amount:
                            payment_entry = self.process_payment_entry(
                                                transaction_record
                                                ,si_doc
                                                ,bank_account
                                                ,settled_amount
                                                ,disallowance_amount)
                           
                            if record.settlement_advice:
                                settlement_advice.set('remark', 'TDS amount is greater than Outstanding Amount')
                       
                        else:
                            payment_entry = self.process_payment_entry(
                                            transaction_record
                                            ,si_doc
                                            ,bank_account
                                            ,settled_amount)
                           
                            if record.settlement_advice:
                                settlement_advice.set('remark', 'Both Disallowed and TDS amount is greater than Outstanding Amount')
                       
                        if payment_entry:
                            self.update_invoice_reference(si_doc.name, payment_entry, record)
                            if record.settlement_advice:
                                settlement_advice.set('status', 'Partially Processed')
 
                        else:
                            if record.settlement_advice:
                                settlement_advice.set('remark', 'Unable to Create Payment Entry')
                                settlement_advice.set('status', 'Warning')

                        if record.settlement_advice:
                            settlement_advice.save()
                       
                    else:
                        payment_entry = self.process_payment_entry(
                                        transaction_record
                                        ,si_doc
                                        ,bank_account
                                        ,settled_amount
                                        ,tds_amount
                                        ,disallowance_amount)
                       
                        if payment_entry:
                            if bank_amount == 0: # Added due to the validation ( settled_amount = allocated_amount )
                                if record.settlement_advice:
                                    settlement_advice.set('status', 'Fully Processed')
                            else:
                                if record.settlement_advice:
                                    settlement_advice.set('status', 'Partially Processed')
                            self.update_invoice_reference(si_doc.name, payment_entry, record)
                        else:
                            if record.settlement_advice:
                                settlement_advice.set('remark','Unable to Create Payment Entry')
                                settlement_advice.set('status', 'Warning')
                       
                        if record.settlement_advice:
                            settlement_advice.save()
               
                except Exception as e:
                    frappe.db.set_value('Matcher', record.name, 'status', 'Error')
                    frappe.db.set_value('Matcher', record.name, 'remarks', e)
 
        frappe.db.commit()
 
 
@frappe.whitelist()
def run_payment_entry(): 
    """"Chunk and matcher logic configurations are handled in Control Panel Side"""
    seq_no = 0 
    chunk_size, m_logic = int(frappe.get_single('Control Panel').payment_matching_chunk_size), tuple(frappe.get_single('Control Panel').match_logic.split(',')) 
    bt_doc_records = frappe.db.sql("""SELECT name, bank_account, reference_number, date FROM `tabBank Transaction`
                                   WHERE name in ( select bank_transaction from `tabMatcher` where match_logic in %(m_logic)s and status = 'Open' )
                                   AND LENGTH(reference_number) > 4 AND status in ('Pending','Unreconciled') AND deposit > 8 ORDER BY unallocated_amount DESC"""
                                   ,values = { "m_logic" : m_logic }
                                   ,as_dict=True)
 
    for record in range(0, len(bt_doc_records), chunk_size):
        seq_no = seq_no + 1
        frappe.enqueue(PaymentEntryCreator().process
                       ,queue='long'
                       ,is_async=True
                       ,job_name="Batch" + str(seq_no)
                       ,timeout=25000
                       ,bt_doc_records = bt_doc_records[record:record + chunk_size]
                       ,match_logic = m_logic)
