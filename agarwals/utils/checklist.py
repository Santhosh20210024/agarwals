import frappe
from agarwals.utils.error_handler import log_error
from erpnext.accounts.utils import get_fiscal_year
from datetime import datetime, timedelta
import pandas as pd
from agarwals.utils.file_util import PROJECT_FOLDER
import os


class checker:
    def __init__(self):
        self.test_cases = {
            'S01': 'Evaluation of claim amounts in sales invoices',
            'S02': 'Evaluation of outstanding amounts and their status in sales invoices',
            'P01': 'Evaluation of allocation amounts in payment entries',
            'P02': 'Evaluation of whether the allocated amount in the bank transaction matches the paid amount in the payment entry',
            'B01': 'Evaluation of the presence of the party and party type in bank transactions',
            'B02': 'Evaluation of unallocated amounts in bank transactions',
            'B03': 'Evaluation of staging total records in bank transactions',
            'SA01': 'Evaluation of settlement advice staging and settlement advice',
            'M01': 'Evaluation of matcher records with status equal to "Open" after the matching process',
            'U01': 'Evaluation of the UTR key in bank transactions',
            'U02': 'Evaluation of the UTR key in settlement advice',
            'U03': 'Evaluation of the UTR key in the claim book',
            'C01': 'Evaluation of presence of claim key in Bill',
            'C02' : 'Evaluation of the presence of claim key in settlement advice',
            'C03' : 'Evaluation of the presence of claim key in Claim Book',
            'B01' : 'Evaluation of all processed bill adjustments has been recorded with a journal entry'
        }

        self.report = []

    def get_sum(self, doctype, field, filter={}):
        sum = frappe.db.get_value(doctype, filter, field, as_dict=True)
        return sum

    def get_count(self, doctype, filter):
        count = frappe.db.count(doctype, filter)
        return count

    def add_to_report(self, case_id, status, reason=''):
        status = 'Passed' if status == True else 'Failed'
        self.report.append({'Name': self.test_cases[case_id], 'Status': status, 'Remarks': reason})

    def get_value(self, value):
        return value if value is not None else 0

    def process_check_list(self, trigger_order):
        if trigger_order:
            trigger_list = {
                "1": "SalesInvoiceChecker",
                "2": "PaymentEntryChecker",
                "3": "BankTransactionChecker",
                "4": "SettlementAdviceChecker",
                "5": "MatcherChecker",
                "6": "UTRKeyChecker",
                "7": 'ClaimKeyChecker',
                "8": 'BillAdjustmentChecker'
            }
            new_order = trigger_order.split(",")
            for order in new_order:
                class_obj = eval(trigger_list[order])()
                class_obj.process()
                self.report.extend(class_obj.report)
        else:
            log_error('There is no trigger_order given')

    def generate_report(self):
        file_name = f'tfs_checklist_{frappe.utils.now_datetime()}.xlsx'
        self.file_path = self.site_path + f"/private/files/{PROJECT_FOLDER}/CheckList/"
        self.report_df = pd.DataFrame(self.report)
        self.report_df.insert(0, 'S NO', range(1, len(self.report) + 1))
        self.report_df.to_excel(self.file_path + file_name, index=False)

    def send_mail(self):
        report_wo_remarks = self.report_df.drop(columns=['Remarks'], axis=1)
        subject = f"TFS:Claimgenie Reconciliation Checklist {frappe.utils.nowdate()}"
        message = f"""
            Hi All,<br>
            Below is the Claimgenie Reconciliation Checklist. 
            <br><br>
            {report_wo_remarks.to_html(header=True, index=False)}
            <br>
            Thanks and regards,
            <br>Claimgenie  
        """
        if self.mail_group:
            recipients = frappe.get_list('Email Group Member', {'email_group': self.mail_group} , pluck='email')
            if recipients:
                frappe.sendmail(recipients=recipients, message=message, subject=subject)
        else:
            log_error('No Mail Group configured')

    def process(self, trigger_order, mail_group, site_path):
        try:
            self.mail_group, self.site_path = mail_group, site_path
            self.process_check_list(trigger_order)
            self.generate_report()
            self.send_mail()
        except Exception as E:
            log_error(E)

class SalesInvoiceChecker(checker):
    def evaluate_si_claim_amount(
            self):  # 2 - Total_Claim_Amount = total_outstanding-amount+ total_allocated_amount + total_credit_amount
        sales_invoice = self.get_sum(doctype='Sales Invoice', filter={'status': ('!=', 'Cancelled')},
                                     field='sum(total) as claim_amount,sum(outstanding_amount) as outstanding')
        payment_entry = self.get_sum(doctype='Payment Entry', filter={'status': 'Submitted'},
                                     field='sum(total_allocated_amount) as allocated')
        je_credit_amount = frappe.db.sql(
            """Select sum(tje.total_credit) as total from `tabJournal Entry` tje WHERE TRIM(SUBSTRING_INDEX(tje.name, '-', -1)) <> 'WB' """,
            pluck='total')
        reconciled_amount = (self.get_value(sales_invoice.outstanding) + self.get_value(
            payment_entry.allocated) + self.get_value(je_credit_amount[0]))
        self.add_to_report('S01', True) if self.get_value(
            sales_invoice.claim_amount) == reconciled_amount else self.add_to_report('S01', False,
                                                                                     f'Claim amount {self.get_value(sales_invoice.claim_amount)} Not equal to reconciled  amount {reconciled_amount}')

    def si_status_check(self):
        si_status_error_list = frappe.db.sql(
            """Select name from `tabSales Invoice` tsi where (tsi.outstanding_amount > 0.01  AND tsi.status = 'Paid') OR (tsi.outstanding_amount < 0.01 AND tsi.status = 'Unpaid')""",
            as_list=True)
        self.add_to_report('S02', True) if not si_status_error_list else self.add_to_report('S02', False,
                                                                                            'Outstanding amount > 0 but status paid or Outstanding amount < 0 but status Unpaid')

    def process(self):
        self.evaluate_si_claim_amount()
        self.si_status_check()


class PaymentEntryChecker(checker):
    def allocated_amount_check(self):  # 4 - Paid_amount +TDS + Disallowance = Total_allocated_amount
        misallocated_payment_entry_query = """
                                SELECT tped.parent AS name,ABS(ROUND(SUM(tped.amount) + tpe.paid_amount) - ROUND(tpe.total_allocated_amount) ) as diff
                                FROM `tabPayment Entry Deduction` tped
                                JOIN `tabPayment Entry` tpe ON tpe.name = tped.parent WHERE tpe.status = 'Submitted' GROUP BY tped.parent
                                HAVING diff > 1;
                              """
        misallocated_payment_entry = frappe.db.sql(misallocated_payment_entry_query, as_dict=True)
        self.add_to_report('P01', False,
                           f'For {len(misallocated_payment_entry)} Paymentry Entry Total Allocated Amount Not Equals to (Paid amount + TDS + Disallowance)') if misallocated_payment_entry else self.add_to_report(
            'P01', True)

    def pe_bt_allocated_amount_check(
            self):  # 6 - Bank Transaction(child_table) allocated_amount = Payment Entry paid amount
        pe_paid_amount = self.get_value(frappe.db.sql(
            "SELECT ROUND(SUM(tpe.paid_amount)) as 'sum_paid'  FROM `tabPayment Entry` tpe WHERE tpe.status = 'Submitted' ",
            pluck='sum_paid')[0])
        bt_allocated_amount = self.get_value(frappe.db.sql(
            "SELECT ROUND(SUM(tbtp.allocated_amount)) as 'sum_allocated' FROM `tabBank Transaction Payments` tbtp WHERE tbtp.payment_document = 'Payment Entry' ",
            pluck='sum_allocated')[0])
        self.add_to_report('P02', True) if (pe_paid_amount - bt_allocated_amount) == 0 else self.add_to_report('P02',
                                                                                                               False,
                                                                                                               f'Bank Transaction Allocated_amount ({bt_allocated_amount[0]}) != ({pe_paid_amount[0]}) Payment Entry paid amount ')

    def process(self):
        self.allocated_amount_check()
        self.pe_bt_allocated_amount_check()


class BankTransactionChecker(checker):
    def party_check(self):  # 7 -  Party & party type in Bank Transaction Should Exist
        bank_transaction_list = frappe.db.sql(
            "Select tbt.name from `tabBank Transaction`tbt where (tbt.party = NULL or tbt.party = '' ) Or (tbt.party_type = NULL or tbt.party_type) = ''",
            as_dict=True)
        self.add_to_report('B01', False,
                           f'In Bank Transaction Field Party or Party type Found Empty') if bank_transaction_list else self.add_to_report(
            'B01', True)

    def unallocated_amount_check(
            self):  # 8 - Bank Transaction unallocated Greater Than 1 And status should not be reconciled vise verse for Unreconciled.
        bank_transaction_list = frappe.db.sql(
            "Select tbt.name from `tabBank Transaction`tbt Where (tbt.status = 'Reconciled' AND tbt.unallocated_amount >= 0.1) OR (tbt.status = 'Unreconciled' AND tbt.unallocated_amount < 0.01)",
            as_dict=True)
        self.add_to_report('B02', False,
                           f'Unallocated Amount > 0 But Status = Reconciled OR  Unallocated Amount < 0 But Status = Unreconciled') if bank_transaction_list else self.add_to_report(
            'B02', True)

    def bt_total_staging_check(
            self):  # 11 - Bank Transaction Staging (Count) Should be Equal to that of the Bank Transaction (Count)
        bt_staging_count = self.get_value(
            self.get_count('Bank Transaction Staging', {'staging_status': ('in', ['Processed', 'Warning'])}))
        bt_count = self.get_value(self.get_count('Bank Transaction', {}))
        self.add_to_report('B03', False,
                           f'Bank Transaction Staging Count ({bt_staging_count}) != ({bt_count} Bank Transaction Count)') if bt_staging_count != bt_count else self.add_to_report(
            'B03', True)

    def process(self):
        self.party_check()
        self.unallocated_amount_check()
        self.bt_total_staging_check()


class SettlementAdviceChecker(checker):
    def sa_total_staging_check(
            self):  # 10 - Settlement Advice Staging (Count) Should be Equal To that of the Settlement Advice (Count)
        sa_count = self.get_value(self.get_count('Settlement Advice', {}))
        sa_staging_count = self.get_value(self.get_count('Settlement Advice Staging', {'status': ('!=', 'Error')}))
        self.add_to_report('SA01', False,
                           f'Settlement Advice Staging total records {sa_staging_count} != {sa_count} Settlement Advice total records') if sa_count != sa_staging_count else self.add_to_report(
            'SA01', True)

    def process(self):
        self.sa_total_staging_check()


class MatcherChecker(checker):
    def matcher_status_check(self):  # 12 - Any  Matcher Document should not be open after the payment_Entry Process.
        open_matcher = self.get_value(self.get_count('Matcher', {'status': 'Open'}))
        self.add_to_report('M01', False,
                           f'There are {open_matcher} Matcher Records found "Status in Open "') if open_matcher != 0 else self.add_to_report(
            'M01', True)

    def process(self):
        self.matcher_status_check()


class UTRKeyChecker(checker):
    def check_utr_key(self):
        bank_transaction = self.get_value(self.get_count('Bank Transaction', {'custom_utr_key': None}))
        settlement_advice = self.get_value(self.get_count('Settlement Advice', {'utr_key': None}))
        claimbook = self.get_value(self.get_count('ClaimBook', {'utr_key': None}))
        self.add_to_report('U01', True) if bank_transaction == 0 else self.add_to_report('U01', False,
                                                                                         f'{bank_transaction} Records Found "UTR KEY = NONE " in Bank_transaction')
        self.add_to_report('U02', True) if settlement_advice == 0 else self.add_to_report('U02', False,
                                                                                          f'{settlement_advice} Records Found "UTR KEY = NONE " in Settlement Advice')
        self.add_to_report('U03', True) if claimbook == 0 else self.add_to_report('U03', False,
                                                                                  f'{claimbook} Records Found "UTR KEY = NONE " in Claim Book')
    def process(self):
        self.check_utr_key()

class ClaimKeyChecker(checker):
    def check_claim_key(self):
        settlement_advice = self.get_value(self.get_count('Settlement Advice', {'claim_key': None}))
        claimbook = self.get_value(frappe.db.sql("SELECT count(1) total FROM `tabClaimBook` WHERE (al_number is NOT NULL AND al_key is NULL) OR (cl_number is NOT null and cl_key IS NULL)",pluck= 'total')[0])
        bill = self.get_value(frappe.db.sql("SELECT count(1) total FROM `tabBill` WHERE (ma_claim_id IS NOT NULL AND ma_claim_key is NULL ) OR (claim_id IS NOT NULL AND (claim_key is NULL AND claim_key <> 0)) "))
        self.add_to_report('C01',True ) if bill == 0 else self.add_to_report('C01', False,f'{bill} Records Found "Claim KEY = NONE " in Bill')
        self.add_to_report('C02',True) if settlement_advice == 0 else self.add_to_report('C02',False,f'{settlement_advice} Records Found "Claim KEY = NONE " in Settlement Advice')
        self.add_to_report('C03',True) if claimbook == 0 else self.add_to_report('C03',False,f'{claimbook} Records Found "Claim KEY = NONE " in Claim Book')

    def process(self):
        self.check_claim_key()

class BillAdjustmentChecker(checker):

    def eval_bill_adjustment_with_jv(self):
        bill_adjustment = self.get_value(self.get_count('Bill Adjustment', {'status': ['in', ['Processed', 'Partially Processed']]}))
        jv_count = self.get_value(frappe.db.sql("""SELECT COUNT(DISTINCT(jv.reference_name)) as total FROM `tabJournal Entry Account` jv JOIN `tabBill Adjustment` ba ON ba.name = jv.reference_name ;""",pluck = 'total')[0])
        self.add_to_report('B01',True ) if bill_adjustment == jv_count else self.add_to_report('B01', False,f'bill adjustment {bill_adjustment} Not Equals to {jv_count} Journal Entry "')

    def process(self):
        self.eval_bill_adjustment_with_jv()

@frappe.whitelist()
def process():
    try:
        control_panel = frappe.get_single("Control Panel")
        if control_panel.site_path is None:
            raise Exception("Site Path Not Found")
        trigger_order = control_panel.order if control_panel.order else "1,2,3,4,5,6,7,8"
        checklist_instance = checker()
        frappe.enqueue(checklist_instance.process, queue='long', job_name=f"checklist - {frappe.utils.now_datetime()}",
                       trigger_order=trigger_order, mail_group=control_panel.check_list_email_group,
                       site_path=control_panel.site_path)
    except Exception as e:
        log_error(f"error While Processing checklist - {e}")

@frappe.whitelist()
def delete_checklist():
    try:
        path = frappe.get_single("Control Panel").site_path + f"/private/files/{PROJECT_FOLDER}/CheckList/"
        if os.path.exists(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        log_error(f"Error deleting file {file_path}: {e}")
        else:
            log_error("Path Not exits")
    except Exception as e:
        log_error(f"Error deleting checklist - {e}")