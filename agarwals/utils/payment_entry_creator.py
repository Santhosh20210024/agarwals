import frappe
import unicodedata
import re


class PaymentEntryCreator:
    def __init__(self,claim_records,bill_records,settlement_advice_records):
        self.claim_records = claim_records
        self.bill_records = bill_records
        self.settlement_advice_records = settlement_advice_records

    def trim_and_remove_leading_zeros(self, text):
        return str(text).strip().lstrip('0')


    def log_error(self, doctype, record_name = None, error_msg = None):
        error_log_record = frappe.new_doc('Payment Entry Error Log')
        error_log_record.set('reference_doctype',doctype)
        if record_name:
            error_log_record.set('reference_record',record_name)

        error_log_record.set('error_message',error_msg)
        error_log_record.save()
        frappe.db.commit()

    def get_document_record(self, doctype, name):
        return frappe.get_doc(doctype,name)

    def get_matched_sa_records(self, reference_number):
        matched_records = []
        for settlement_advice_record in self.settlement_advice_records:
            utr_number = self.trim_and_remove_leading_zeros(settlement_advice_record['utr_number'])
            final_utr_number = self.trim_and_remove_leading_zeros(settlement_advice_record['final_utr_number'])
            if utr_number != reference_number and final_utr_number != reference_number:
                continue
            elif reference_number == utr_number:
                matched_records.append(settlement_advice_record)
            elif reference_number == final_utr_number:
                matched_records.append(settlement_advice_record)
        return matched_records

    def format_bill_no(self,bill_no):
        return bill_no.strip().lower().replace(':','')

    def get_bill_record_with_bill_no(self, bill_no):
        bill_no = self.format_bill_no(bill_no)
        for record in self.bill_records:
            dbr_bill_no = self.format_bill_no(record['name'])
            if bill_no == dbr_bill_no:
                return record
        return None

    def get_variant_claim_numbers(self,claim_id):
        claim_id = unicodedata.normalize("NFKD", claim_id)
        variant_claim_number = []
        claim_id = claim_id.strip()
        variant_claim_number.append(claim_id)
        possible_claim_id = re.sub(r'-?\((\d)\)$', '', claim_id)
        variant_claim_number.append(possible_claim_id)
        formatted_claim_id = claim_id.lower().replace(' ', '').replace('.', '').replace('alnumber', '').replace(
            'number', '').replace(
            'alno', '').replace('al-', '').replace('ccn', '').replace('id:', '').replace('orderid:', '').replace(':',
                                                                                                                 '').replace(
            '(', '').replace(')', '')
        variant_claim_number.append(formatted_claim_id)
        possible_claim_id = re.sub(r'-(\d)(\d)?$', '', formatted_claim_id)
        variant_claim_number.append(possible_claim_id)
        possible_claim_id = re.sub(r'-(\d)(\d)?$', r'\1\2', formatted_claim_id)
        variant_claim_number.append(possible_claim_id)
        possible_claim_id = re.sub(r'_(\d)(\d)?$', '', formatted_claim_id)
        variant_claim_number.append(possible_claim_id)
        possible_claim_id = re.sub(r'_(\d)(\d)?$', r'\1\2', formatted_claim_id)
        variant_claim_number.append(possible_claim_id)
        return set(variant_claim_number)

    def match_with_claimbook_and_bill(self,sa_record,bank_utr,match_log, match_with,order):
        matched_bills = []
        matched_claims = []
        matched_cb_records = None
        matched_bill_records = None
        claim_records_matched = False
        sa_claim_numbers = self.get_variant_claim_numbers(sa_record.claim_id)
        for record in self.claim_records:
            if not record[match_with]:
                continue
            cb_claim_numbers = self.get_variant_claim_numbers(record[match_with])
            matched_claim_numbers = sa_claim_numbers.intersection(cb_claim_numbers)
            if not matched_claim_numbers:
                continue
            claim_records_matched = True
            if not record['custom_raw_bill_number']:
                match_log.append({
                    'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_claim[{sa_record.claim_id}] > cb_{match_with}[{record[match_with]}] > cb_bill_no[Not found]",
                    'status': 'Fail', 'order': order + 1})
                continue
            cb_bill_no = self.format_bill_no(record['custom_raw_bill_number'])
            for bill_record in self.bill_records:
                bill_no = self.format_bill_no(bill_record['name'])
                if bill_no == cb_bill_no:
                    if not bill_record['claim_id']:
                        match_log.append({
                            'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_claim[{sa_record.claim_id}] > cb_{match_with}[{record[match_with]}] > cb_bill_no[{record['custom_raw_bill_number']}] > dbr_bill_no[{bill_record['name']}] > dbr_claim[No claim Id]",
                            'status': 'Fail', 'order': order + 1})
                        continue
                    bill_claim_numbers = self.get_variant_claim_numbers(bill_record['claim_id'])
                    matched_bill_records = bill_claim_numbers.intersection(cb_claim_numbers)
                    if not matched_bill_records:
                        match_log.append({
                            'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_claim[{sa_record.claim_id}] > cb_{match_with}[{record[match_with]}] > cb_bill_no[{record['custom_raw_bill_number']}] > dbr_bill_no[{bill_record['name']}] > dbr_claim[{bill_record['claim_id']}] > Not matched",
                            'status': 'Fail', 'order': order + 1})
                        continue
                    matched_bills.append(bill_record)
                    matched_claims.append(record)
                    match_log.append({
                        'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_claim[{sa_record.claim_id}] > cb_{match_with}[{record[match_with]}] > cb_bill_no[{record['custom_raw_bill_number']}] > dbr_bill_no[{bill_record['name']}] > dbr_claim[{bill_record['claim_id']}] > Matched",
                        'status': 'Success', 'order': order + 1})
        return matched_bills,matched_claims,claim_records_matched,match_log

    def match_with_bill(self,sa_record,bank_utr,match_log,order):
        matched_bills = []
        matched_bill_records = None
        sa_claim_numbers = self.get_variant_claim_numbers(sa_record.claim_id)
        for record in self.bill_records:
            if not record['claim_id']:
                continue
            bill_claim_numbers = self.get_variant_claim_numbers(record['claim_id'])
            matched_bill_records = sa_claim_numbers.intersection(bill_claim_numbers)
            if matched_bill_records:
                matched_bills.append(record)
                match_log.append({
                    'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_claim[{sa_record.claim_id}] > dbr_claim[{record['claim_id']}] > Matched",
                    'status': 'Success', 'order': order + 1})
        return matched_bills, match_log

    def get_matched_bill_and_claim(self,sa_record,bank_utr):
        match_log = []
        matched_bill = []
        matched_claim = []
        # If Bill No in Settlement Advice trying to match with Debtors Bill No
        if sa_record.bill_no:
            bill_record = self.get_bill_record_with_bill_no(sa_record.bill_no)
            if bill_record:
                match_log.append({
                    'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_bill[{sa_record.bill_no}] > dbr_bill[{bill_record['name']}] > Matched",
                    'status': 'Success', 'order': 1})
                return bill_record, None, match_log
            match_log.append({
                                 'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_bill[{sa_record.bill_no}] > dbr_bill[no bill record]",
                                 'status': 'Fail', 'order': 1})
        match_log.append({
            'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_bill[No bill number]",
            'status': 'Fail', 'order': 1})
        matched_bill, matched_claim,claim_records_matched, match_log = self.match_with_claimbook_and_bill(sa_record,bank_utr,match_log,'al_number',1)
        if matched_bill:
            if len(matched_bill) == 1:
                return matched_bill[0], matched_claim[0], match_log
            sa_record.set('remark',str(sa_record.remark) + '\nMore than 1 bill Matched')
            sa_record.save()
        if not claim_records_matched:
            match_log.append({
                'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_claim[{sa_record.claim_id}] > cb_al[No claim Record Found]",
                'status': 'Fail', 'order': 2})
        matched_bill, matched_claim,claim_records_matched, match_log = self.match_with_claimbook_and_bill(sa_record, bank_utr, match_log,
                                                                                    'cl_number', 2)
        if matched_bill:
            if len(matched_bill) == 1:
                return matched_bill[0], matched_claim[0], match_log
            sa_record.set('remark', str(sa_record.remark) + '\nMore than 1 bill Matched')
            sa_record.save()
        if not claim_records_matched:
            match_log.append({
                'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_claim[{sa_record.claim_id}] > cb_cl[No claim Record Found]",
                'status': 'Fail', 'order': 3})
        matched_bill, match_log = self.match_with_bill(sa_record, bank_utr, match_log, 3)
        if not matched_bill:
            match_log.append({
                'log': f"bank_utr[{bank_utr}] > sa_utr[{sa_record.utr_number}] > sa_claim[{sa_record.claim_id}] > dbr_claim[No Bill Record Found]",
                'status': 'Fail', 'order': 4})
            return None, None, match_log
        if len(matched_bill) > 1:
            sa_record.set('remark', str(sa_record.remark) + '\nMore than 1 bill Matched')
            sa_record.save()
            return None, None, match_log
        return matched_bill[0], None, match_log

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
            if disallowed_amount > 0:
                deductions.append({'account': 'Disallowance - A', 'cost_center': sales_invoice.cost_center,
                                   'description': 'Disallowance',
                                   'branch': sales_invoice.branch, 'entity': sales_invoice.entity,
                                   'region': sales_invoice.region, 'branch_type': sales_invoice.branch_type,
                                   'amount': disallowed_amount})
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
            bank_transaction.append('payment_entries',
                                    {'payment_document': 'Payment Entry', 'payment_entry': payment_entry_record.name,
                                     'allocated_amount': payment_entry_record.paid_amount})
            bank_transaction.submit()
            frappe.db.commit()
            return payment_entry_record.name
        except Exception as e:
            self.log_error('Sales Invoice',sales_invoice.name,error_msg=e)
            return ''


    def add_match_log(self,match_logs,settlement_advice_record):
        match_logs = sorted(match_logs, key=lambda x:x['order'])
        match_log_list = []
        for match_log in match_logs:
            match_log_list.append({'status':match_log['status'], 'log':match_log['log']})
        settlement_advice_record.set('match_log',match_log_list)
        settlement_advice_record.save()
        frappe.db.commit()

    def get_company_account(self, bank_account_name):
        bank_account = frappe.get_doc('Bank Account', bank_account_name)
        if not bank_account.account:
            return None
        return bank_account.account

    def process(self, bank_transaction_records):
        for bank_transaction_record in bank_transaction_records:
            if not bank_transaction_record['date']:  #If Date is null skip to next record
                self.log_error('Bank Transaction', bank_transaction_record['name'], "Date is Null")
                continue
            bank_account = self.get_company_account(bank_transaction_record['bank_account'])
            if not bank_account:  #If Company Bank Account is not found skip to next record
                self.log_error('Bank Transaction', bank_transaction_record['name'], "No Company Account Found")
                continue
            utr_number = self.trim_and_remove_leading_zeros(bank_transaction_record['reference_number']) #trim and removing leading zeros in utr number
            matched_sa_records = self.get_matched_sa_records(utr_number) #Getting matched settlement advice records using utr number
            if not matched_sa_records: #If no settlement advice records matched with utr number skip to next record
                frappe.db.set_value('Bank Transaction', bank_transaction_record['name'], 'custom_advice_status',
                                    'Not Found')
                frappe.db.commit()
                continue
            frappe.db.set_value('Bank Transaction', bank_transaction_record['name'], 'custom_advice_status',
                                'Found')
            frappe.db.commit()
            matched_sa_records = sorted(matched_sa_records,
                                                       key=lambda x: (x['tds_amount'], x['disallowed_amount']),
                                                       reverse=True) #Sort the Settlement Advice with TDS Amount and then Disallowed Amount
            for record in matched_sa_records:
                bank_amount = 0
                settlement_advice = self.get_document_record('Settlement Advice',record['name'])
                if settlement_advice.settled_amount == settlement_advice.claim_amount:
                    settled_amount = settlement_advice.settled_amount - settlement_advice.tds_amount - settlement_advice.disallowed_amount
                    tds_amount = settlement_advice.tds_amount
                    disallowed_amount = abs(settlement_advice.disallowed_amount)
                else:
                    settled_amount = settlement_advice.settled_amount
                    tds_amount = settlement_advice.tds_amount
                    disallowed_amount = abs(settlement_advice.disallowed_amount)
                bank_transaction = self.get_document_record('Bank Transaction',bank_transaction_record['name'])
                if bank_transaction.unallocated_amount == 0:
                    break
                if settled_amount > bank_transaction.unallocated_amount:
                    settled_amount = bank_transaction.unallocated_amount
                    bank_amount = bank_transaction.unallocated_amount
                matched_bill,matched_claim,match_log = self.get_matched_bill_and_claim(settlement_advice,bank_transaction.reference_number)
                if not matched_bill:
                    self.add_match_log(match_log, settlement_advice)
                    settlement_advice.set('status', 'Error')
                    settlement_advice.set('matched_bank_transaction', bank_transaction_record.name)
                    settlement_advice.save()
                    frappe.db.commit()
                    continue
                sales_invoice = self.get_document_record('Sales Invoice', matched_bill['name'])
                if matched_claim:
                    self.add_match_log(match_log, settlement_advice)
                    settlement_advice.set('matched_bank_transaction', bank_transaction.name)
                    settlement_advice.set('matched_claimbook_record', matched_claim['name'])
                    settlement_advice.set('matched_bill_record', matched_bill['name'])
                    settlement_advice.save()
                    frappe.db.set_value('ClaimBook',matched_claim['name'],'matched_status','Matched')
                    frappe.db.set_value('Sales Invoice', sales_invoice.name, 'custom_insurance_name',
                                        matched_claim['insurance_company_name'])
                    frappe.db.commit()
                else:
                    self.add_match_log(match_log, settlement_advice)
                    settlement_advice.set('matched_bank_transaction', bank_transaction.name)
                    settlement_advice.set('matched_bill_record', matched_bill['name'])
                    settlement_advice.save()
                    frappe.db.commit()
                if sales_invoice.outstanding_amount < settled_amount:
                    self.log_error('Settlement Advice', settlement_advice.name,
                                   "Settled amount is greater than Outstanding Amount")
                    settlement_advice.set('status', 'Not Processed')
                    settlement_advice.set('remark', 'Settled amount is greater than Outstanding Amount')
                    settlement_advice.save()
                    frappe.db.commit()
                elif sales_invoice.outstanding_amount < settled_amount + tds_amount + disallowed_amount:
                    if sales_invoice.outstanding_amount >= settled_amount + tds_amount:
                        payment_entry_created = self.create_payment_entry_and_update_bank_transaction(
                            bank_transaction, sales_invoice, bank_account, settled_amount,
                            tds_amount)
                        settlement_advice.set('remark', 'Disallowance amount is greater than Outstanding Amount')
                    elif sales_invoice.outstanding_amount >= settled_amount + disallowed_amount:
                        payment_entry_created = self.create_payment_entry_and_update_bank_transaction(
                            bank_transaction,
                            sales_invoice, bank_account,
                            settled_amount, disallowed_amount)
                        settlement_advice.set('remark', 'TDS amount is greater than Outstanding Amount')
                    else:
                        payment_entry_created = self.create_payment_entry_and_update_bank_transaction(
                            bank_transaction,
                            sales_invoice, bank_account,
                            settled_amount)
                        settlement_advice.set('remark', 'Both Disallowed and TDS amount is greater than Outstanding Amount')
                    if payment_entry_created:
                        settlement_advice.set('status', 'Partially Processed')
                    else:
                        settlement_advice.set('remark', 'Unable to Create Payment Entry')
                        settlement_advice.set('status', 'Warning')
                    settlement_advice.save()
                    frappe.db.commit()
                else:
                    payment_entry_name = self.create_payment_entry_and_update_bank_transaction(
                        bank_transaction,
                        sales_invoice, bank_account,
                        settled_amount, tds_amount, disallowed_amount)
                    if payment_entry_name:
                        if bank_amount == 0:
                            settlement_advice.set('status', 'Fully Processed')
                        else:
                            settlement_advice.set('status', 'Partially Processed')
                        sales_invoice.append('custom_reference',{'payment_entry':payment_entry_name})
                        frappe.db.commit()
                    else:
                        settlement_advice.set('remark','Unable to Create Payment Entry')
                        settlement_advice.set('status', 'Warning')
                    settlement_advice.save()
                    frappe.db.commit()
