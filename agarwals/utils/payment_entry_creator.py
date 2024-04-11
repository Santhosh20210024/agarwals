import frappe
import unicodedata
import re
from frappe.utils.caching import redis_cache

class PaymentEntryCreator:

    def log_error(self, doctype, record_name = None, error_msg = None):
        error_log_record = frappe.new_doc('Payment Entry Error Log')
        error_log_record.set('reference_doctype',doctype)
        if record_name:
            error_log_record.set('reference_record',record_name)

        error_log_record.set('error_message',error_msg)
        error_log_record.save()

    def check_writeoff(self, payment_entry_record, sales_invoice):
        if payment_entry_record.difference_amount > 0:
            payment_entry_record.set('deductions', {'account': 'Write Off - A', 'cost_center': sales_invoice.cost_center,
                                   'description': 'Write Off',
                                   'branch': sales_invoice.branch, 'entity': sales_invoice.entity,
                                   'region': sales_invoice.region, 'branch_type': sales_invoice.branch_type,
                                   'amount': payment_entry_record.difference_amount} )
            return payment_entry_record
        return payment_entry_record

    def create_payment_entry_and_update_bank_transaction(self, bank_transaction, sales_invoice, bank_account, settled_amount, tds_amount = 0, disallowed_amount = 0):
        payment_entries_for_same_bill = frappe.get_list('Payment Entry', filters={'custom_sales_invoice':sales_invoice.name})
        if payment_entries_for_same_bill:
            name = sales_invoice.name + "-" +str(len(payment_entries_for_same_bill))
        else:
            name = sales_invoice.name
        try:
            deductions = []
            payment_entry_record = frappe.new_doc('Payment Entry')
            payment_entry_record.set('name',name)
            payment_entry_record.set('custom_sales_invoice', sales_invoice.name)
            payment_entry_record.set('payment_type', 'Receive')
            payment_entry_record.set('posting_date', bank_transaction.date)
            payment_entry_record.set('mode_of_payment', 'Bank Draft')
            payment_entry_record.set('party_type', 'Customer')
            payment_entry_record.set('party', sales_invoice.customer)
            payment_entry_record.set('bank_account', bank_transaction.bank_account)
            payment_entry_record.set('paid_to', bank_account)
            payment_entry_record.set('paid_from', 'Debtors - A')
            payment_entry_record.set('paid_amount', settled_amount)
            payment_entry_record.set('received_amount', settled_amount)
            payment_entry_record.set('reference_no', bank_transaction.reference_number)
            payment_entry_record.set('reference_date', bank_transaction.date)
            payment_entry_record.set('cost_center', sales_invoice.cost_center)
            payment_entry_record.set('branch', sales_invoice.branch)
            payment_entry_record.set('entity', sales_invoice.entity)
            payment_entry_record.set('region', sales_invoice.region)
            payment_entry_record.set('branch_type', sales_invoice.branch_type)
            if tds_amount > 0:
                deductions.append({'account': 'TDS - A', 'cost_center': sales_invoice.cost_center, 'description': 'TDS',
                                   'branch': sales_invoice.branch, 'entity': sales_invoice.entity,
                                   'region': sales_invoice.region, 'branch_type': sales_invoice.branch_type,
                                   'amount': tds_amount})
                payment_entry_record.set('custom_tds_amount', tds_amount)
            if disallowed_amount > 0:
                deductions.append({'account': 'Disallowance - A', 'cost_center': sales_invoice.cost_center,
                                   'description': 'Disallowance',
                                   'branch': sales_invoice.branch, 'entity': sales_invoice.entity,
                                   'region': sales_invoice.region, 'branch_type': sales_invoice.branch_type,
                                   'amount': disallowed_amount})
                payment_entry_record.set('custom_disallowed_amount', disallowed_amount)

            if deductions:
                payment_entry_record.set('deductions', deductions)

            reference_item = [{
                'reference_doctype': 'Sales Invoice',
                'reference_name': sales_invoice.name,
                'allocated_amount': settled_amount + tds_amount + disallowed_amount
            }]

            payment_entry_record.set('references', reference_item)
            payment_entry_record.save()
            payment_entry_record = self.check_writeoff(payment_entry_record, sales_invoice)
            payment_entry_record.submit()

            bank_transaction = frappe.get_doc('Bank Transaction', bank_transaction.name)
            bank_transaction.append('payment_entries',
                                    {'payment_document': 'Payment Entry', 'payment_entry': payment_entry_record.name,
                                     'allocated_amount': payment_entry_record.paid_amount})
            bank_transaction.submit()
            frappe.db.commit()
            return payment_entry_record
        
        except Exception as e:
            self.log_error('Sales Invoice', sales_invoice.name, error_msg=e)
            return ''

    def get_document_record(self, doctype, name):
        return frappe.get_doc(doctype,name)


    @redis_cache
    def get_company_account(self, bank_account_name):
        bank_account = frappe.get_doc('Bank Account', bank_account_name)
        if not bank_account.account:
            return None
        return bank_account.account
    
    def update_payment_reference(self, sales_invoice, payment_entry, record):
        sales_doc = self.get_document_record('Sales Invoice', sales_invoice)
        sales_doc.append('custom_reference',{'payment_entry':payment_entry.name,'paid_amount':payment_entry.paid_amount, 
                                                            'tds_amount':payment_entry.custom_tds_amount, 'disallowance_amount':payment_entry.custom_disallowed_amount, 
                                                            'allocated_amount':payment_entry.total_allocated_amount, 'utr_number':payment_entry.reference_no })
        
        sales_doc.append('custom_matcher_reference', {'id' : record.name, 'match_logic' : record.match_logic, 'settlement_advice': record.settlement_advice})
        frappe.db.set_value('Matcher', record.name, 'status', 'Processed')
        sales_doc.save()

    def process(self, bank_transaction_records, match_logic):
    
        for bank_transaction_record in bank_transaction_records:
            if not bank_transaction_record['date']: 
                self.log_error('Bank Transaction', bank_transaction_record['name'], "Date is Null")
                continue

            bank_account = self.get_company_account(bank_transaction_record['bank_account'])
            if not bank_account:
                self.log_error('Bank Transaction', bank_transaction_record['name'], "No Company Account Found")
                continue

            matcher_records = frappe.db.sql("""
                          SELECT * from `tabMatcher` where match_logic in %(logic)s AND bank_transaction = %(reference_number)s AND status is NULL order by payment_order ASC, tds_amount DESC , disallowance_amount DESC
                          """, values = {'reference_number' : bank_transaction_record.name, 'logic': match_logic}, as_dict = True)

            if matcher_records:
                frappe.db.set_value('Bank Transaction', bank_transaction_record['name'], 'custom_advice_status','Found')

            for record in matcher_records:
                try:
                    bank_amount = 0
                    if record.settled_amount:
                        settled_amount = float(record.settled_amount)
                    else:
                        settled_amount = 0 
                    if record.tds_amount:
                        tds_amount = float(record.tds_amount)
                    else:
                        tds_amount = 0
                    if record.disallowance_amount:
                        disallowance_amount = float(record.disallowance_amount)
                    else:
                        disallowance_amount = 0
                    unallocated_amount = self.get_document_record('Bank Transaction', record.bank_transaction).unallocated_amount
                    
                    if record.settlement_advice:
                        settlement_advice = self.get_document_record('Settlement Advice', record.settlement_advice)
                    
                    if unallocated_amount == 0:
                        break

                    if settled_amount > unallocated_amount:
                        settled_amount = unallocated_amount
                        bank_amount = unallocated_amount

                    sales_invoice = self.get_document_record('Sales Invoice', record.sales_invoice)

                    if record.claimbook:
                        if record.settlement_advice:
                            settlement_advice.set('insurance_company_name', record.insurance_company_name)
                            settlement_advice.set('matched_bank_transaction', bank_transaction_record['name'])
                            settlement_advice.set('matched_claimbook_record', record.claimbook)
                            settlement_advice.set('matched_bill_record', record.sales_invoice)
                        frappe.db.set_value('ClaimBook',record.claimbook,'matched_status','Matched')
                        frappe.db.set_value('Sales Invoice', sales_invoice.name, 'custom_insurance_name', record.insurance_company_name)
                    else:
                        if record.settlement_advice:
                            settlement_advice.set('matched_bank_transaction', bank_transaction_record['name'])
                            settlement_advice.set('matched_bill_record',record.sales_invoice)

                    if record.settlement_advice:
                        settlement_advice.set('tpa', sales_invoice.customer)
                        settlement_advice.set('region', sales_invoice.region)
                        settlement_advice.set('entity', sales_invoice.entity)
                        settlement_advice.set('branch_type', sales_invoice.branch_type)

                    if sales_invoice.outstanding_amount < settled_amount:
                        settled_amount = sales_invoice.outstanding_amount

                    if sales_invoice.outstanding_amount < settled_amount + tds_amount + disallowance_amount:
                        
                        if sales_invoice.outstanding_amount >= settled_amount + tds_amount:
                            payment_entry = self.create_payment_entry_and_update_bank_transaction(
                                bank_transaction_record, sales_invoice, bank_account, settled_amount,
                                tds_amount)
                            if record.settlement_advice:
                                settlement_advice.set('remark', 'Disallowance amount is greater than Outstanding Amount')
                        
                        elif sales_invoice.outstanding_amount >= settled_amount + disallowance_amount:
                            payment_entry = self.create_payment_entry_and_update_bank_transaction(
                                bank_transaction_record,
                                sales_invoice, bank_account,
                                settled_amount, disallowance_amount)
                            if record.settlement_advice:
                                settlement_advice.set('remark', 'TDS amount is greater than Outstanding Amount')
                        
                        else:
                            payment_entry = self.create_payment_entry_and_update_bank_transaction(
                                bank_transaction_record,
                                sales_invoice, bank_account,
                                settled_amount)
                            if record.settlement_advice:
                                settlement_advice.set('remark', 'Both Disallowed and TDS amount is greater than Outstanding Amount')
                        
                        if payment_entry:
                            self.update_payment_reference(sales_invoice.name, payment_entry, record)
                            if record.settlement_advice:
                                settlement_advice.set('status', 'Partially Processed')
                        else:
                            if record.settlement_advice:
                                settlement_advice.set('remark', 'Unable to Create Payment Entry')
                                settlement_advice.set('status', 'Warning')
                        if record.settlement_advice:
                            settlement_advice.save()
                        
                    else:
                        payment_entry = self.create_payment_entry_and_update_bank_transaction(
                            bank_transaction_record,
                            sales_invoice, bank_account,
                            settled_amount, tds_amount, disallowance_amount)
                        if payment_entry:
                            if bank_amount == 0: #?
                                if record.settlement_advice:
                                    settlement_advice.set('status', 'Fully Processed')
                            else:
                                if record.settlement_advice:
                                    settlement_advice.set('status', 'Partially Processed')
                            
                            self.update_payment_reference(sales_invoice.name, payment_entry, record)
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

    batch_number = 0
    n = int(frappe.get_single('Control Panel').payment_matching_chunk_size)
    match_logic = tuple(frappe.get_single('Control Panel').match_logic.split(','))

    # Need to change as X00
    bank_transaction_records = frappe.db.sql(f"SELECT name, bank_account, reference_number, date FROM `tabBank Transaction` WHERE name in (select bank_transaction from `tabMatcher` where match_logic in {match_logic} and status is null ) AND status IN ('Pending','Unreconciled') AND LENGTH(reference_number) > 4 AND deposit > 10 AND reference_number not like 'X0%' ORDER BY unallocated_amount DESC", as_dict=True)

    for i in range(0, len(bank_transaction_records), n):
        batch_number = batch_number + 1
        frappe.enqueue(PaymentEntryCreator().process, queue='long', is_async=True, job_name="Batch" + str(batch_number), timeout=25000,
                       bank_transaction_records = bank_transaction_records[i:i + n], match_logic = match_logic)