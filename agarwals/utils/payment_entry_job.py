import frappe
import traceback
import re
import unicodedata
from fuzzywuzzy import fuzz


class BankTransactionWrapper():

    def __init__(self, bank_transaction):
        self.bank_transaction = bank_transaction
        self.available_amount = bank_transaction.deposit
        self.advice_log = {"bnk.utr": '', "sa.utr": '', "sa.bill": '', "sa.claim": '', "cb.al": '', "cb.cl": '',
                           "dbr.claim": '', "dbr.bill": ''}
        self.claim_records = frappe.db.sql('SELECT name, al_number, cl_number, custom_raw_bill_number, insurance_name FROM `tabClaimBook`', as_dict = True)
        self.debtors_records = frappe.db.sql('SELECT name, claim_id FROM `tabBill` WHERE status != "CANCELLED"' ,as_dict = True)
        self.minimum_matching_percentage = int(frappe.get_single('Control Panel').minimum_matching_percentage)

    def clear_advice_log(self):
        for log in self.advice_log:
            self.advice_log[log] = ''

    def add_log_entries(self, advice_name):
        advice_doc = frappe.get_doc("Settlement Advice", advice_name)
        advice_doc.match_log = []
        # Verify whether the advice is already passed
        frappe.db.sql('DELETE FROM `tabMatch Log` WHERE parent = %(parent)s', values={'parent': advice_name})
        frappe.db.commit()

        flow = ''
        for log in self.advice_log.keys():
            if self.advice_log[log] == None:
                continue
            if 'Fail' in self.advice_log[log]:
                advice_doc.append("match_log", {'status': 'Fail',
                                                'log': f'{flow} {log}({str(self.advice_log[log])})'})
            else:
                if self.advice_log[log] != '':
                    flow += f' {log}({self.advice_log[log]}) -> '

        if 'dbr.bill' in flow:
            if not flow.endswith('(Fail)'):
                advice_doc.append("match_log", {'status': 'Success',
                                                'log': f'{flow}'})

        # advice_doc.match_log = match_log
        advice_doc.save()
        frappe.db.commit()

    def sales_utr_entry(self, bank_je_ac):
        bank_invoice_list = [je.reference_name for je in bank_je_ac if je.account == 'Debtors - A']
        invoice_list = bank_invoice_list

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
                self.error_log(
                    user_error_msg=f'Not able to find the bank account for this transaction {self.bank_transaction.reference_number}')
                frappe.db.commit()
                return

                # bank reference trimming
            bnk_ref_num = str(self.bank_transaction.reference_number).strip().lstrip('0')

            # Two way check ( system generated UTR and original UTR only taken the non processed )
            advices = frappe.db.sql("""
                       SELECT * FROM `tabSettlement Advice` WHERE final_utr_number = %(final_utr_number)s 
                       and status != 'Processed' and claim_id != 0 """, values={'final_utr_number': bnk_ref_num},
                                    as_dict=1)

            advices_org_utr = frappe.db.sql("""
                               SELECT * from `tabSettlement Advice` where TRIM(TRIM(LEADING '0' FROM utr_number)) = %(utr_number)s
                               and status != 'Processed' and claim_id != 0""", values={'utr_number': bnk_ref_num},
                                            as_dict=1)

            _flag = False
            if not advices:
                if len(advices_org_utr) > 0:
                    advices = advices_org_utr
                    _flag = True

            # Advice Intial Validation,
            # Status in bank transaction
            if len(advices) < 1:
                self.bank_transaction.custom_advice_status = 'Not Found'
                self.bank_transaction.save()
                frappe.db.commit()
                return
            else:
                self.bank_transaction.custom_advice_status = 'Found'
                self.bank_transaction.save()

            frappe.db.commit()

            bank_je = frappe.new_doc('Journal Entry')
            tds_je = frappe.new_doc('Journal Entry')
            dis_je = frappe.new_doc('Journal Entry')

            bank_je.accounts = []
            tds_je.accounts = []
            dis_je.accounts = []

            # created for the settlement advice reference field in JE
            bank_je_advices = []
            tds_je_advices = []
            dis_je_advices = []

            # upto this validate
            for advice in advices:
                self.clear_advice_log()

                if advice.status == 'Error':  # clear the existing logs
                    frappe.db.set_value('Settlement Advice', advice.name, 'status', '')
                    frappe.db.set_value('Settlement Advice', advice.name, 'remark', '')
                    frappe.db.commit()

                if not (advice.claim_id or advice.bill_no):
                    continue

                if self.available_amount <= 0:
                    break

                # bank utr log
                self.advice_log["bnk.utr"] = self.bank_transaction.reference_number
                self.advice_log['sa.bill'] = advice.bill_no
                self.advice_log['sa.claim'] = advice.claim_id

                if _flag == True:  # only for log value
                    self.advice_log["sa.utr"] = advice['utr_number']
                else:
                    self.advice_log["sa.utr"] = advice['final_utr_number']

                # no error upto this
                entry = self.create_bank_entry(advice)
                self.add_log_entries(advice.name)
                frappe.db.commit()

                if entry:
                    bank_je.append('accounts', entry)
                    bank_je_advices.append(advice.name)
                else:
                    continue

            if bank_je.accounts != None and len(bank_je.accounts) > 0:
                allocated_amount = self.bank_transaction.deposit - self.available_amount
                asset_entry = {'account': self.bank_account, 'debit_in_account_currency': allocated_amount}
                bank_je.append('accounts', asset_entry)
                bank_je.voucher_type = 'Bank Entry'
                bank_je.company = frappe.get_value("Global Defaults", None, "default_company")
                bank_je.posting_date = self.bank_transaction.date
                bank_je.cheque_date = self.bank_transaction.date
                bank_je.cheque_no = self.bank_transaction.name
                bank_je.custom_bank_reference = self.bank_transaction.reference_number
                bank_je.name = self.bank_transaction.reference_number
                bank_je = self.get_advice_obj_list(bank_je_advices, bank_je, 'Bank Entry')
                bank_je.submit()
                self.set_transaction_reference(bank_je.name, allocated_amount)

            _count = 0
            bank_je_list = [bank for bank in bank_je.accounts if bank.account == 'Debtors - A']
            for bje_entry in bank_je_list:
                tds_entry = self.create_tds_entry_item(bje_entry, bank_je_advices[_count])
                if tds_entry != None:
                    tds_je.append('accounts', tds_entry[0])
                    tds_je.append('accounts', tds_entry[1])
                    tds_je_advices.append(bank_je_advices[_count])
                _count += 1

            if tds_je.accounts != None and len(tds_je.accounts) > 0:
                self.create_tds_entries(tds_je, tds_je_advices)

            _count = 0
            for bje_entry in bank_je_list:
                dis_entry = self.create_dis_entry_item(bje_entry, bank_je_advices[_count])
                if dis_entry != None:
                    dis_je.append('accounts', dis_entry[0])
                    dis_je.append('accounts', dis_entry[1])
                    dis_je_advices.append(bank_je_advices[_count])
                _count += 1

            if dis_je.accounts != None and len(dis_je.accounts) > 0:
                self.create_dis_entries(dis_je, dis_je_advices)

            if len(bank_je.accounts) > 0:
                self.sales_utr_entry(bank_je.accounts)

            for advice in bank_je_advices:
                # if len(tds_je_advices) > 0:
                #     if advice in tds_je_advices:
                #         if len(dis_je_advices) > 0:

                # #     e
                # for i
                #     if advice in tds_je_advices and advice in dis_je_advices:
                #         frappe.set_value('Settlement Advice', advice, 'status', 'Fully Processed')
                #     else:
                frappe.set_value('Settlement Advice', advice, 'status', 'Processed')
                frappe.db.commit()

        except Exception as error:
            self.error_log(system_error_msg=error, bank_utr=self.bank_transaction.reference_number)

    def get_advice_obj_list(self, advices, je_doc, tag):
        je_doc.custom_settlement_advice_reference = []
        for advice in advices:
            je_doc.append("custom_settlement_advice_reference", {
                "advices": advice,
                "parenttype": 'Journal Entry',
                "parent": je_doc.name
            })

            advice_doc = frappe.get_doc('Settlement Advice', advice)
            if (advice_doc.processed_entries == None):
                advice_doc.processed_entries = ''
            if tag not in advice_doc.processed_entries:
                advice_doc.processed_entries += f'{tag}, '
                advice_doc.save()
                frappe.db.commit()

        return je_doc

    def create_tds_entries(self, tds_je, tds_je_advices):
        try:
            name_ref = self.bank_transaction.reference_number or self.bank_transaction.name
            tds_je.name = str(name_ref) + "-" + "TDS"
            tds_je.voucher_type = 'Credit Note'
            tds_je.company = frappe.get_value("Global Defaults", None, "default_company")
            tds_je.posting_date = self.bank_transaction.date
            tds_je.cheque_date = self.bank_transaction.date
            tds_je.cheque_no = str(name_ref)
            tds_je.submit()
            tds_je = self.get_advice_obj_list(tds_je_advices, tds_je, 'TDS Entry')

        except Exception as e:
            self.error_log(user_error_msg='Error acquired during tds entry creation bank_reference =' + str(
                self.bank_transaction.name))
            return

            # disallowance amount entry

    def create_dis_entries(self, dis_je, dis_je_advices):
        try:
            name_ref = self.bank_transaction.reference_number or self.bank_transaction.name
            tds_je.name = str(name_ref) + "-" + "DIS"
            tds_je.voucher_type = 'Credit Note'
            tds_je.company = frappe.get_value("Global Defaults", None, "default_company")
            tds_je.posting_date = self.bank_transaction.date
            tds_je.cheque_date = self.bank_transaction.date
            tds_je = self.get_advice_obj_list(dis_je_advices, dis_je, 'DIS Entry')
            tds_je.cheque_no = str(name_ref)
            tds_je.submit()

        except Exception as e:
            self.error_log(user_error_msg='Error acquired during dis entry creation bank_reference =' + str(
                self.bank_transaction.name))
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

    def get_matched_record(self, key, value, search_records):
        matched_records = []
        for record in search_records:
            if record[key]:
                matching_percentage = int(fuzz.ratio(value, record[key]))
                if matching_percentage > self.minimum_matching_percentage:
                    matched_records.append(claim_record)
        return matched_records

    def get_matched_bill_number_and_insurance_name(self,claim_records,debtors,log_key,claim_key):
        for claim_record in claim_records:
            for debtor_record in debtors:
                if claim_record['custom_raw_bill_number']:
                    if claim_record['custom_raw_bill_number'].lower().strip().replace(' ', '') == debtor_record[
                        'name'].lower().strip().replace(' ', ''):
                        self.advice_log[log_key] = str(claim_record[claim_key])
                        return debtor_record['name'],debtor_record['claim_id'],claim_record['insurance_name']
        return None, None,None

    def check_claim(self, advice, claim_id):  # only based on claim id
        matched_bill_number = None
        insurance_name = None
        matched_debtor_claim_number = None

        debtors = self.get_matched_records('claim_id',claim_id, self.debtors_records)
        claims_al = self.get_matched_records('al_number', claim_id, self.claim_records)
        claims_cl = self.get_matched_record('cl_number', claim_id,self.claim_records)

        if debtors:
            if claims_al:
                matched_bill_number, matched_debtor_claim_number, insurance_name = self.get_matched_bill_number_and_insurance_name(claims_al,debtors,'cb.al','al_number')
            if not matched_bill_number and claims_cl:
                self.advice_log[log_key] = 'Fail'
                matched_bill_number, matched_debtor_claim_number, insurance_name = self.get_matched_bill_number_and_insurance_name(claims_cl,
                                                                                                      debtors, 'cb.cl',
                                                                                                      'cl_number')
            if not matched_bill_number:
                self.advice_log['cb.cl'] = 'Fail'

        # Final Validation
        if matched_bill_number:
            self.advice_log['dbr.claim'] = matched_debtor_claim_number
            return matched_bill_number, insurance_name

        else:
            self.error_log(advice, user_error_msg=f"No claim exists: {str(claim_id)}")
            return matched_bill_number, insurance_name

    # Done

    def get_sales_invoice(self, advice, bill_number):
        try:
            return frappe.get_doc('Sales Invoice', bill_number)
        except:
            self.error_log(advice, user_error_msg=f"No Sales Invoice Found: {str(bill_number)}")
            return None

    def create_bank_entry(self, advice):  # done

        if (self.available_amount <= 0):
            return None, None

        # sales invoice number
        invoice_number = None
        sales_invoice = 0
        insurance_name = None

        # checking on both advices' bill no and claim id
        if advice.bill_no:
            if len(frappe.get_list('Bill', filters={'name':advice.bill_no})) == 1:
                invoice_number = advice.bill_no

        if not invoice_number:
            matched_bill_number, insurance_name = self.check_claim(advice, advice.claim_id)

            if matched_bill_number:
                invoice_number = matched_bill_number
                insurance_name = insurance_name

        if invoice_number:
            sales_invoice = self.get_sales_invoice(advice, invoice_number)
            if sales_invoice:
                self.advice_log['dbr.bill'] = sales_invoice.name
            else:
                self.advice_log['dbr.bill'] += f' (Fail)'  # need to check
                return None
        else:
            return None

        if self.available_amount >= advice.settled_amount:
            if advice.settled_amount <= sales_invoice.outstanding_amount:
                allocated_amount = advice.settled_amount
            else:
                self.error_log(advice,
                               user_error_msg="Settlement Amount is greater than the Outstanding Amount for " + str(
                                   invoice_number))
                return None
        else:
            allocated_amount = self.available_amount
        self.available_amount = self.available_amount - allocated_amount

        entry = {
            'account': 'Debtors - A',
            'party_type': 'Customer',
            'party': sales_invoice.customer,
            'credit_in_account_currency': allocated_amount,
            'reference_type': 'Sales Invoice',
            'reference_name': sales_invoice.name,
            'reference_due_date': sales_invoice.posting_date,
            'region': sales_invoice.region,
            'entity': sales_invoice.entity,
            'branch': sales_invoice.branch,
            'cost_center': sales_invoice.cost_center,
            'branch_type': sales_invoice.branch_type
        }

        if insurance_name != None:
            invoice = frappe.get_doc('Sales Invoice', sales_invoice.name)
            invoice.append('custom_insurance_company_name',
                           {'insurance_name': insurance_name, "parenttype": 'Sales Invoice',
                            "parent": sales_invoice.name})
            invoice.save()
            frappe.db.commit()

            frappe.db.sql("""UPDATE `tabSettlement Advice` 
                             SET region = %(region)s, 
                             entity = %(entity)s, 
                             branch_type = %(branch_type)s,
                             tpa = %(customer)s, 
                             insurance_company_name = %(insurance)s
                             where name = %(name)s """,
                          values={'region': sales_invoice['region'],
                                  'entity': sales_invoice['entity'],
                                  'branch_type': sales_invoice['branch_type'],
                                  'customer': sales_invoice['customer'],
                                  'insurance': insurance_name,
                                  'name': advice.name},
                          as_dict=True)

        frappe.db.commit()
        return entry

    def create_tds_entry_item(self, entry, advice):
        advice = frappe.get_doc('Settlement Advice', advice)
        sales_invoice = frappe.get_doc('Sales Invoice', entry.reference_name)

        if advice.tds_amount:
            if advice.tds_amount > sales_invoice.outstanding_amount:  # extra added
                self.error_log(advice,
                               user_error_msg=f'TDS entry Failed: {advice.name}({advice.tds_amount}) is greater than Debtor ({sales_invoice.name})({sales_invoice.outstanding_amount})/n')
                return None

            tds_entry = [
                {
                    'account': 'Debtors - A',
                    'party_type': 'Customer',
                    'party': sales_invoice.customer,
                    'credit_in_account_currency': advice.tds_amount,
                    'reference_type': 'Sales Invoice',
                    'reference_name': sales_invoice.name,
                    'reference_due_date': sales_invoice.posting_date,
                    'user_remark': 'tds credits',
                    'region': sales_invoice.region,
                    'entity': sales_invoice.entity,
                    'branch': sales_invoice.branch,
                    'cost_center': sales_invoice.cost_center,
                    'branch_type': sales_invoice.branch_type
                },
                {
                    'account': 'TDS Credits - A',
                    'party_type': 'Customer',
                    'party': sales_invoice.customer,
                    'debit_in_account_currency': advice.tds_amount,
                    'region': sales_invoice.region,
                    'user_remark': 'tds debits',
                    'region': sales_invoice.region,
                    'entity': sales_invoice.entity,
                    'branch': sales_invoice.branch,
                    'cost_center': sales_invoice.cost_center,
                    'branch_type': sales_invoice.branch_type
                }
            ]
            advice.save()
            return tds_entry

        return None

    def create_dis_entry_item(self, entry, advice):
        advice = frappe.get_doc('Settlement Advice', advice)
        sales_invoice = frappe.get_doc('Sales Invoice', entry.reference_name)

        if advice.disallowed_amount:
            if advice.disallowed_amount > sales_invoice.outstanding_amount:
                self.error_log(advice,
                               user_error_msg=f'TDS entry Failed: {advice.name}({advice.tds_amount}) is greater than Debtor ({sales_invoice.name})({sales_invoice.outstanding_amount})/n')
                return None

            dis_entry = [
                {
                    'account': 'Debtors - A',
                    'party_type': 'Customer',
                    'party': sales_invoice.customer,
                    'credit_in_account_currency': advice.disallowed_amount,
                    'reference_type': 'Sales Invoice',
                    'reference_name': sales_invoice.name,
                    'reference_due_date': sales_invoice.posting_date,
                    'user_remark': 'tds credits',
                    'region': sales_invoice.region,
                    'entity': sales_invoice.entity,
                    'branch': sales_invoice.branch,
                    'cost_center': sales_invoice.cost_center,
                    'branch_type': sales_invoice.branch_type
                },
                {
                    'account': 'DIS Credits - A',
                    'party_type': 'Customer',
                    'party': sales_invoice.customer,
                    'debit_in_account_currency': advice.disallowed_amount,
                    'region': sales_invoice.region,
                    'user_remark': 'tds debits',
                    'region': sales_invoice.region,
                    'entity': sales_invoice.entity,
                    'branch': sales_invoice.branch,
                    'cost_center': sales_invoice.cost_center,
                    'branch_type': sales_invoice.branch_type
                }
            ]

            advice.save()
            return dis_entry

        return None

    def error_log(self, advice=None, system_error_msg=None, user_error_msg=None, bank_utr=None):
        error_record_doc = frappe.new_doc('Error Record Log')
        error_record_doc.doctype_name = "Journal Entry"

        if advice != None:
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
        frappe.db.commit()


def payment_batch_operation(chunk):
    for record in chunk:
        transaction_doc = frappe.get_doc("Bank Transaction", record)
        transaction = BankTransactionWrapper(transaction_doc)
        transaction.process()


def get_unreconciled_bank_transactions():
    # checks on deposit, status reference_number and allocated amount > 10
    return frappe.db.sql("""
    SELECT name FROM `tabBank Transaction` WHERE status in ('unreconciled', 'pending') AND deposit > 0 AND deposit is NOT NULL AND LENGTH(reference_number) > 1 AND reference_number != '0' AND unallocated_amount > 10""",
                         as_dict=1)


@frappe.whitelist()
def create_payment_entries():
    unreconciled_bank_transactions = get_unreconciled_bank_transactions()
    pending_transactions = []
    for bank_transaction in unreconciled_bank_transactions:
        pending_transactions.append(bank_transaction.name)
        # transaction_doc = frappe.get_doc("Bank Transaction", bank_transaction.name)
        # transaction = BankTransactionWrapper(transaction_doc)
        # transaction.process()

    chunk_size = 1000
    for i in range(0, len(pending_transactions), chunk_size):
        frappe.enqueue(payment_batch_operation, queue='long', is_async=True, timeout=18000,
                       chunk=pending_transactions[i:i + chunk_size])