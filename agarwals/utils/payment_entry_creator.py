import frappe

class PaymentEntryCreator:
    def __init__(self):
        self.bank_transaction_records = frappe.db.sql("SELECT name, bank_account, reference_number, date FROM `tabBank Transaction` WHERE status IN ('Pending','Unreconciled') AND deposit != 0 AND LENGTH(reference_number) > 5 AND deposit > 10",as_dict=True)
        self.claim_records = frappe.db.sql(
            "SELECT name, al_number, cl_number, custom_raw_bill_number, insurance_company_name FROM `tabClaimBook`",
            as_dict=True)
        self.debtors_records = frappe.db.sql("SELECT name, claim_id FROM `tabBill` WHERE status != 'CANCELLED'",
                                             as_dict=True)
        self.settlement_advice_records = frappe.db.sql("SELECT name, claim_id, utr_number, final_utr_number, settled_amount, tds_amount, disallowed_amount FROM `tabSettlement Advice` WHERE status = 'Open'", as_dict = True)

    def get_company_account(self, bank_account_name):
        bank_account = frappe.get_doc('Bank Account', bank_account_name)
        if not bank_account.account:
            return None
        return bank_account.account

    def log_error(self, doctype, record_name, error_msg):
        error_log_record = frappe.new_doc('Payment Entry Error Log')
        error_log_record.set('reference_doctype',doctype)
        error_log_record.set('reference_name',record_name)
        error_log_record.set('error_message',error_msg)
        error_log_record.save()
        frappe.db.commit()

    def strip_leading_zeros(self, text):
        return str(text).strip().lstrip('0')

    def get_matched_advice_records(self, reference_number):
        matched_records = []
        for settlement_advice_record in self.settlement_advice_records:
            utr_number = self.strip_leading_zeros(settlement_advice_record['utr_number'])
            final_utr_number = self.strip_leading_zeros(settlement_advice_record['final_utr_number'])
            if reference_number != utr_number or reference_number != final_utr_number:
                continue
            elif reference_number == utr_number:
                matched_records.append(settlement_advice_record)
                continue
            elif reference_number == final_utr_number:
                matched_records.append(settlement_advice_record)
        return matched_records

    def get_settlement_advice_record(self,name):
        return frappe.get_doc('Settlement Advice', name)

    def get_bank_transaction_record(self, name):
        return frappe.get_doc('Bank Transaction', name)

    def get_bill_record(self,name):
        try:
            bill_record = frappe.get_doc('Bill', name)
            return bill_record
        except:
            return None

    def get_sales_invoice_record(self, name):
        return frappe.get_doc('Sales Invoice', name)

    def get_possible_claim_ids(self, claim_id):
        claim_id = unicodedata.normalize("NFKD", claim_id)
        possible_claim_numbers = []
        possible_claim_numbers.append(claim_id)
        possible_claim_id = re.sub(r'-?\((\d)\)$', '', claim_id)
        possible_claim_numbers.append(possible_claim_id)
        formatted_claim_id = claim_id.lower().replace(' ', '').replace('.', '').replace('alnumber', '').replace(
            'number', '').replace(
            'alno', '').replace('al-', '').replace('ccn', '').replace('id:', '').replace('orderid:', '').replace(':',
                                                                                                                 '').replace(
            '(', '').replace(')', '')
        possible_claim_numbers.append(formatted_claim_id)
        possible_claim_id = re.sub(r'-(\d)(\d)?$', '', formatted_claim_id)
        possible_claim_numbers.append(possible_claim_id)
        possible_claim_id = re.sub(r'-(\d)(\d)?$', r'\1\2', formatted_claim_id)
        possible_claim_numbers.append(possible_claim_id)
        possible_claim_id = re.sub(r'_(\d)(\d)?$', '', formatted_claim_id)
        possible_claim_numbers.append(possible_claim_id)
        possible_claim_id = re.sub(r'_(\d)(\d)?$', r'\1\2', formatted_claim_id)
        possible_claim_numbers.append(possible_claim_id)
        return set(possible_claim_numbers)

    def get_matched_claim_book_records(self, settlement_advice_claim_ids, match_with):
        matched_records = []
        for claim_record in self.claim_records:
            claim_book_claim_ids = self.get_possible_claim_ids(claim_record[match_with])
            matched_claim_ids = settlement_advice_claim_ids.intersection(claim_book_claim_ids)
            if len(matched_claim_ids) > 0:
                matched_records.append(claim_record)
        return matched_records

    def get_matched_debtor_records(self,settlement_advice_claim_ids):
        matched_records = []
        for debtor_record in self.debtors_records:
            claim_ids = self.get_possible_claim_ids(debtor_record['claim_id'])
            matched_claim_ids = settlement_advice_claim_ids.intersection(claim_ids)
            if len(matched_claim_ids) > 0:
                matched_records.append(debtor_record)
        return matched_records

    def get_matched_bill_and_logs(self, settlement_advice_record, bank_transaction_utr_number):
        match_log = []
        matched_bill_record = []
        matched_claim_record = []
        if settlement_advice_record.bill_no:
            formatted_bill_no = self.strip_leading_zeros(settlement_advice_record.bill_no)
            formatted_bill_no = formatted_bill_no.replace(':','')
            bill_record = self.get_bill_record(formatted_bill_no)
            if bill_record:
                match_log.append({'log' : f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_bill[{settlement_advice_record.bill_no}] > dbr_bill[{bill_record.bill_no}]', 'status':'Success', 'order': 1})
                return bill_record,None, match_log
            match_log.append({'log' : f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_bill[{settlement_advice_record.bill_no}] > dbr_bill[no bill record]', 'status':'Fail', 'order':1})
        match_log.append({
                             'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_bill[no bill number]',
                             'status': 'Fail', 'order': 1})
        settlement_advice_record_possible_claim_ids = self.get_possible_claim_ids(settlement_advice_record.claim_id)
        claim_book_records_matched_with_al = self.get_matched_claim_book_records(settlement_advice_record_possible_claim_ids,'al_number')
        if not claim_book_records_matched_with_al:
            match_log.append({
                                 'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > cb_al_number[no claimbook record]',
                                 'status': 'Fail', 'order': 2})
            claim_book_records_matched_with_cl = self.get_matched_claim_book_records(settlement_advice_record_possible_claim_ids,'cl_number')
            if not claim_book_records_matched_with_cl:
                match_log.append({
                                     'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > cb_cl_number[no claimbook record]',
                                     'status': 'Fail', 'order': 3})
                debtors_records_with_claim_id = self.get_matched_debtor_records(settlement_advice_record_possible_claim_ids)
                if not debtors_records_with_claim_id:
                    match_log.append({
                        'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > dbr_claim_id[no bill record]',
                        'status': 'Fail', 'order': 4})
                    return None, None, match_log
                if len(debtors_records_with_claim_id) > 1:
                    match_log.append({
                        'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > dbr_claim_id[more than 1 record found]',
                        'status': 'Fail', 'order': 4})
                    return None, None, match_log
                match_log.append({
                    'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > dbr_claim_id[{debtors_records_with_claim_id[0]['claim_id']}] > dbr_bill_number[{debtors_records_with_claim_id[0]['name']}]',
                    'status': 'Success', 'order': 4})
                return debtors_records_with_claim_id[0] ,None, match_log
            for claim_book_record in claim_book_records_matched_with_cl:
                formatted_bill_no = self.strip_leading_zeros(claim_book_record['custom_raw_bill_number'])
                formatted_bill_no = formatted_bill_no.replace(':', '').lower()
                for debtor_record in self.debtors_records:
                    if formatted_bill_no == debtor_record['name'].strip().lower():
                        matched_bill_record.append(debtor_record)
                        matched_claim_record.append(claim_book_record)
            if len(matched_bill_record) > 1:
                match_log.append({
                    'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > cb_cl_number[more than 1 record found]',
                    'status': 'Fail', 'order': 3})
                return None, None, match_log
            elif len(matched_bill_record) == 1:
                match_log.append({
                    'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > cb_cl_number[{matched_claim_record[0]['cl_number']}] > cb_final_bill_number[{matched_claim_record[0]['custom_raw_bill_number']}] > dbr_bill_number[{matched_bill_record[0]['name']}]',
                    'status': 'Success', 'order': 3})
                return matched_bill_record[0], matched_claim_record[0], match_log
        for claim_book_record in claim_book_records_matched_with_al:
            formatted_bill_no = self.strip_leading_zeros(claim_book_record['custom_raw_bill_number'])
            formatted_bill_no = formatted_bill_no.replace(':', '').lower()
            for debtor_record in self.debtors_records:
                if formatted_bill_no == debtor_record['name'].strip().lower():
                    matched_bill_record.append(debtor_record)
                    matched_claim_record.append(claim_book_record)
        if len(matched_bill_record) > 1:
            match_log.append({
                'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > cb_al_number[more than 1 record found]',
                'status': 'Fail', 'order': 2})
            return None, None, match_log
        elif len(matched_bill_record) == 1:
            match_log.append({
                'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > cb_al_number[{matched_claim_record[0]['cl_number']}] > cb_final_bill_number[{matched_claim_record[0]['custom_raw_bill_number']}] > dbr_bill_number[{matched_bill_record[0]['name']}]',
                'status': 'Success', 'order': 2})
            return matched_bill_record[0],matched_claim_record[0], match_log
        match_log.append({
            'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > matched_with_claimbook_but_not_matched_with_debtor',
            'status': 'Success', 'order': 2})
        debtors_records_with_claim_id = self.get_matched_debtor_records(settlement_advice_record_possible_claim_ids)
        if not debtors_records_with_claim_id:
            match_log.append({
                'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > dbr_claim_id[no bill record]',
                'status': 'Fail', 'order': 3})
            return None, None, match_log
        if len(debtors_records_with_claim_id) > 1:
            match_log.append({
                'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > dbr_claim_id[more than 1 record found]',
                'status': 'Fail', 'order': 3})
            return None, None, match_log
        match_log.append({
            'log': f'bank_utr[{bank_transaction_utr_number}] > sa_utr[{settlement_advice_record.utr_number}] > sa_claim_id[{settlement_advice_record.claim_id}] > dbr_claim_id[{debtors_records_with_claim_id[0]['claim_id']}] > dbr_bill_number[{debtors_records_with_claim_id[0]['name']}]',
            'status': 'Success', 'order': 3})
        return debtors_records_with_claim_id[0],None, match_log

    def add_match_log(self,match_logs,settlement_advice_record):
        match_logs = sorted(match_logs, key=lambda x:x['order'])
        match_log_list = []
        for match_log in match_logs:
            match_log_list.append({'status':match_log['status'], 'log':match_log['log']})
        settlement_advice_record.set('match_log',match_log_list)
        settlement_advice_record.save()
        frappe.db.commit()

    def strip_leading_zeros(self, bank_transaction, sales_invoice, bank_account, settled_amount, tds_amount = 0, disallowed_amount = 0):
        deductions = []
        payment_entry_record = frappe.new_doc('Payment Entry')
        payment_entry_record.set('custom_sales_invoice',sales_invoice.name)
        payment_entry_record.set('payment_type', 'Receive')
        payment_entry_record.set('posting_date', bank_transaction.date)
        payment_entry_record.set('mode_of_payment','Bank Draft') #Need to verify
        payment_entry_record.set('party_type', 'Customer')
        payment_entry_record.set('party',sales_invoice.customer)
        payment_entry_record.set('bank_account', bank_transaction.bank_account)
        payment_entry_record.set('paid_to',bank_account)
        payment_entry_record.set('paid_from', 'Debtors - A')
        payment_entry_record.set('paid_amount',settled_amount)
        payment_entry_record.set('received_amount',settled_amount)
        payment_entry_record.set('reference_no',bank_transaction.reference_number)
        payment_entry_record.set('reference_date',bank_transaction.date)
        if tds_amount > 0:
            deductions.append({'account': 'TDS - A','cost_center':sales_invoice.cost_center,'description':'TDS','branch':sales_invoice.branch,'entity':sales_invoice.entity,'region':sales_invoice.region,'branch_type':sales_invoice.branch_type})
        if disallowed_amount > 0:
            deductions.append({'account': 'Disallowance - A', 'cost_center': sales_invoice.cost_center, 'description': 'Disallowance',
                               'branch': sales_invoice.branch, 'entity': sales_invoice.entity,
                               'region': sales_invoice.region, 'branch_type': sales_invoice.branch_type})
        if deductions:
            payment_entry_record.set('deductions',deductions)
        reference_item = [{
            'reference_doctype': 'Sales Invoice',
            'reference_name': sales_invoice.name,
            'allocated_amount': settled_amount + tds_amount + disallowed_amount
        }]
        payment_entry_record.set('references',reference_item)
        payment_entry_record.save()
        payment_entry_record.submit()

        bank_transaction.append('payment_entries',{'payment_document':'Payment Entry','payment_entry':payment_entry_record.name,'allocated_amount':payment_entry_record.paid_amount})
        bank_transaction.submit()
        frappe.db.commit()


    def create_payment_entry(self, matched_settlement_advice_records, bank_transaction_record_name, bank_account):
        for matched_settlement_advice_record in matched_settlement_advice_records:
            settlement_advice_record = self.get_settlement_advice_record(matched_settlement_advice_record['name'])
            if settlement_advice_record.settled_amount == settlement_advice_record.claim_amount:
                settled_amount = settlement_advice_record.settled_amount - settlement_advice_record.tds_amount - settlement_advice_record.disallowed_amount
                tds_amount = settlement_advice_record.tds_amount
                disallowed_amount = abs(settlement_advice_record.disallowed_amount)
            else:
                settled_amount = settlement_advice_record.settled_amount
                tds_amount = settlement_advice_record.tds_amount
                disallowed_amount = abs(settlement_advice_record.disallowed_amount)
            bank_transaction_record = self.get_bank_transaction_record(bank_transaction_record_name)
            if settled_amount > bank_transaction_record.unallocated_amount:
                return
            matched_bill, matched_claim, match_logs = self.get_matched_bill_and_logs(settlement_advice_record, bank_transaction_record.reference_number)
            if not matched_bill:
                self.add_match_log(match_logs,settlement_advice_record)
                settlement_advice_record.set('status','Error')
                settlement_advice_record.set('matched_bank_transaction',bank_transaction_record.name)
                settlement_advice_record.save()
                frappe.db.commit()
                continue
            if matched_claim:
                self.add_match_log(match_logs, settlement_advice_record)
                settlement_advice_record.set('matched_bank_transaction', bank_transaction_record.name)
                settlement_advice_record.set('matched_claimbook_record', matched_claim['name'])
                settlement_advice_record.set('matched_bill_record', matched_bill['name'])
                settlement_advice_record.save()
                frappe.db.commit()
            else:
                self.add_match_log(match_logs, settlement_advice_record)
                settlement_advice_record.set('matched_bank_transaction', bank_transaction_record.name)
                settlement_advice_record.set('matched_bill_record', matched_bill['name'])
                settlement_advice_record.save()
                frappe.db.commit()
            matched_sales_invoice_record = self.get_sales_invoice_record(matched_bill['name'])
            frappe.db.set_value('Sales Invoice',matched_sales_invoice_record.name, 'custom_insurance_name',matched_claim['insurance_company_name'])
            if matched_sales_invoice_record.outstanding_amount < settled_amount:
                self.log_error('Settlement Advice', settlement_advice_record['name'], "Settled amount is greater than Outstanding Amount")
                settlement_advice_record.set('status', 'Not Processed')
                settlement_advice_record.set('remark','Settled amount is greater than Outstanding Amount')
                settlement_advice_record.save()
                frappe.db.commit()
            elif matched_sales_invoice_record.outstanding_amount < settled_amount + tds_amount + disallowed_amount:
                if matched_sales_invoice_record.outstanding_amount >= settled_amount + tds_amount:
                    self.strip_leading_zeros(bank_transaction_record, matched_sales_invoice_record, bank_account, settled_amount, tds_amount)
                    settlement_advice_record.set('remark', 'Disallowance amount is greater than Outstanding Amount')
                else:
                    self.strip_leading_zeros(bank_transaction_record,
                                                     matched_sales_invoice_record, bank_account,
                                                     settled_amount, disallowed_amount)
                    settlement_advice_record.set('remark', 'TDS amount is greater than Outstanding Amount')
                settlement_advice_record.set('status','Partially Processed')
                settlement_advice_record.save()
                frappe.db.commit()
            else:
                self.strip_leading_zeros(bank_transaction_record,
                                                 matched_sales_invoice_record, bank_account,
                                                 settled_amount, tds_amount, disallowed_amount)
                settlement_advice_record.set('status', 'Fully Processed')
                settlement_advice_record.save()
                frappe.db.commit()

    def process(self, bank_transaction_records):
        for bank_transaction_record in bank_transaction_records:
            bank_account = self.get_company_account(bank_transaction_record['bank_account'])
            if not bank_account:
                self.log_error('Bank Transaction', bank_transaction_record['name'], "No Company Account Found")
                continue
            reference_number = self.strip_leading_zeros(bank_transaction_record['reference_number'])
            matched_advice_records = self.get_matched_advice_records(reference_number)
           
            if not matched_advice_records:
                frappe.db.set_value('Bank Transaction',bank_transaction_record['name'], 'cg_status', 'Not Found')
                self.log_error('Bank Transaction', bank_transaction_record['name'], "No Settlement Advices Found")
                continue
            else:
                frappe.db.set_value('Bank Transaction',bank_transaction_record['name'], 'cg_status', 'Found')

            matched_advice_records = sorted(matched_advice_records, key=lambda x:(x['tds_amount'],x['disallowed_amount']), reverse = True)
            self.create_payment_entry(matched_advice_records, bank_transaction_record['name'], bank_account)

# Need to check for the bank status