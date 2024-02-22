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
            payment_entry_record.set('mode_of_payment', 'Bank Draft')  # Need to verify
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
    def get_company_account(self, bank_account_name): # need to be cache
        bank_account = frappe.get_doc('Bank Account', bank_account_name)
        if not bank_account.account:
            return None
        return bank_account.account
    
    def update_payment_reference(self, sales_invoice, payment_entry):
        sales_doc = self.get_document_record('Sales Invoice', sales_invoice)
        sales_doc.append('custom_reference',{'payment_entry':payment_entry.name,'paid_amount':payment_entry.paid_amount,
                                                             'tds_amount':payment_entry.custom_tds_amount, 'disallowance_amount':payment_entry.custom_disallowed_amount,
                                                             'allocated_amount':payment_entry.total_allocated_amount, 'utr_number':payment_entry.reference_no })
        sales_doc.save()

    def process(self, bank_transaction_records):
        match_logic = frappe.get_single('Control Panel').match_logic.split(',') # neeed to replace

        for bank_transaction_record in bank_transaction_records:
            if not bank_transaction_record['date']:  #If Date is null skip to next record
                self.log_error('Bank Transaction', bank_transaction_record['name'], "Date is Null")
                continue

            bank_account = self.get_company_account(bank_transaction_record['bank_account'])
            if not bank_account:  #If Company Bank Account is not found skip to next record
                self.log_error('Bank Transaction', bank_transaction_record['name'], "No Company Account Found")
                continue

            # matching table logic
            matcher_records = frappe.db.sql("""
                                SELECT * from `tabMatcher` where match_logic in %(logic)s AND bank_transaction = %(reference_number)s order by tds_amount DESC , disallowance_amount DESC
                          """, values = {'reference_number' : bank_transaction_record.name, 'logic': tuple(match_logic)}, as_dict = True)

            if matcher_records:
                frappe.db.set_value('Bank Transaction', bank_transaction_record['name'], 'custom_advice_status','Found')


            for record in matcher_records:
                bank_amount = 0
                settled_amount = float(record.settled_amount)
                tds_amount = float(record.tds_amount)
                disallowance_amount = float(record.disallowance_amount)
                unallocated_amount = frappe.get_doc('Bank Transaction', record.bank_transaction).unallocated_amount
                settlement_advice = self.get_document_record('Settlement Advice', record.settlement_advice)

                
                if unallocated_amount == 0:
                    break

                if settled_amount > unallocated_amount:
                    settled_amount = unallocated_amount
                    bank_amount = unallocated_amount

                sales_invoice = self.get_document_record('Sales Invoice', record.sales_invoice)

                if record.claimbook:
                    settlement_advice.set('insurance_company_name', record.insurance_company_name)
                    settlement_advice.set('matched_bank_transaction', bank_transaction_record['name'])
                    settlement_advice.set('matched_claimbook_record', record.claimbook)
                    settlement_advice.set('matched_bill_record', record.sales_invoice)
                    frappe.db.set_value('ClaimBook',record.claimbook,'matched_status','Matched')
                    frappe.db.set_value('Sales Invoice', sales_invoice.name, 'custom_insurance_name',
                                        record.insurance_company_name)
                else:
                    settlement_advice.set('matched_bank_transaction', bank_transaction_record['name'])
                    settlement_advice.set('matched_bill_record',record.sales_invoice)

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
                        settlement_advice.set('remark', 'Disallowance amount is greater than Outstanding Amount')
                    elif sales_invoice.outstanding_amount >= settled_amount + disallowance_amount:
                        payment_entry = self.create_payment_entry_and_update_bank_transaction(
                            bank_transaction_record,
                            sales_invoice, bank_account,
                            settled_amount, disallowance_amount)
                        settlement_advice.set('remark', 'TDS amount is greater than Outstanding Amount')
                    else:
                        payment_entry = self.create_payment_entry_and_update_bank_transaction(
                            bank_transaction_record,
                            sales_invoice, bank_account,
                            settled_amount)
                        settlement_advice.set('remark', 'Both Disallowed and TDS amount is greater than Outstanding Amount')
                    if payment_entry:
                        self.update_payment_reference(sales_invoice.name, payment_entry)
                        settlement_advice.set('status', 'Partially Processed')
                    else:
                        settlement_advice.set('matched_bank_transaction', bank_transaction_record['name'])
                        settlement_advice.set('matched_bill_record',record.sales_invoice)
                    
                    settlement_advice.set('tpa', sales_invoice.customer)
                    settlement_advice.set('region', sales_invoice.region)
                    settlement_advice.set('entity', sales_invoice.entity)
                    settlement_advice.set('branch_type', sales_invoice.branch_type)
                    settlement_advice.save()

                    if sales_invoice.outstanding_amount < settled_amount:
                        settled_amount = sales_invoice.outstanding_amount

                    if sales_invoice.outstanding_amount < settled_amount + tds_amount + disallowance_amount:
                        if sales_invoice.outstanding_amount >= settled_amount + tds_amount:
                            payment_entry = self.create_payment_entry_and_update_bank_transaction(
                                bank_transaction_record, sales_invoice, bank_account, settled_amount,
                                tds_amount)
                            settlement_advice.set('remark', 'Disallowance amount is greater than Outstanding Amount')
                        elif sales_invoice.outstanding_amount >= settled_amount + disallowance_amount:
                            payment_entry = self.create_payment_entry_and_update_bank_transaction(
                                bank_transaction_record,
                                sales_invoice, bank_account,
                                settled_amount, disallowance_amount)
                            settlement_advice.set('remark', 'TDS amount is greater than Outstanding Amount')
                        else:
                            payment_entry = self.create_payment_entry_and_update_bank_transaction(
                                bank_transaction_record,
                                sales_invoice, bank_account,
                                settled_amount)
                            settlement_advice.set('remark', 'Both Disallowed and TDS amount is greater than Outstanding Amount')
                        if payment_entry:
                            self.update_payment_reference(sales_invoice.name, payment_entry)
                            settlement_advice.set('status', 'Partially Processed')
                        else:
                            settlement_advice.set('remark', 'Unable to Create Payment Entry')
                            settlement_advice.set('status', 'Warning')
                        
                        settlement_advice.save()
                    else:
                        payment_entry = self.create_payment_entry_and_update_bank_transaction(
                            bank_transaction_record,
                            sales_invoice, bank_account,
                            settled_amount, tds_amount, disallowance_amount)
                        if payment_entry:
                            if bank_amount == 0:
                                settlement_advice.set('status', 'Fully Processed')
                            else:
                                settlement_advice.set('status', 'Partially Processed')
                            
                            self.update_payment_reference(sales_invoice.name, payment_entry)
                        else:
                            settlement_advice.set('remark','Unable to Create Payment Entry')
                            settlement_advice.set('status', 'Warning')
                        
                        frappe.db.set_value('Matcher', record.name, 'status', 'Success')
                        settlement_advice.save()
                except Exception as e:
                    frappe.db.set_value('Matcher', record.name, 'status', 'Error')
                    frappe.db.set_value('Matcher', record.name, 'remarks', e)

        frappe.db.commit()