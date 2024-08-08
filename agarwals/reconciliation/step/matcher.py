import frappe
from agarwals.utils.updater import update_bill_no_separate_column
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from agarwals.utils.index_update import update_index
from agarwals.utils.matcher_query_list import get_matcher_query

"""
'Open' -> New Records
'Warning' -> Validation Error
'Fully Processed' -> Processed Records
'Partially Processed' -> Partially Processed Records
'Error' -> System Error
'Unmatched' -> Unmatched Records For Other Queries
"""
 
class MatcherValidation:
    def __init__(self, record):
        self.record = record
 
    def is_valid(self):
        return (self._validate_advice() and
                self._validate_amount() and
                self._validate_bill_status() and
                self._validate_bank_transaction())
 
    def _validate_advice(self):
        if self.record['advice'] and self.record.status not in ('Open', 'Not Processed'):
            return False
        return True
   
    @staticmethod
    def round_off(amount):
        if amount:
            return round(float(amount),2)
        else:
          return float(0)
 
    def _validate_amount(self):
        claim_amount = MatcherValidation.round_off(self.record.claim_amount)
        settled_amount = MatcherValidation.round_off(self.record.settled_amount)
        tds_amount = MatcherValidation.round_off(self.record.tds_amount)
        disallowed_amount = MatcherValidation.round_off(self.record.disallowed_amount)
 
        if claim_amount <= 0:
            if self.record['advice']:
                Matcher.update_advice_status(self.record['advice'], 'Warning', 'Claim Amount should not be 0')
            return False
        
        elif settled_amount <= 0:
            if self.record['advice']:
                Matcher.update_advice_status(self.record['advice'], 'Warning', 'Settled Amount should not be 0')
            return False
        
        elif claim_amount and (settled_amount or tds_amount or disallowed_amount ):
            if claim_amount < settled_amount + tds_amount + disallowed_amount:
                Matcher.update_advice_status(self.record['advice'], 'Warning', "Claim Amount is greater than the sum of Settled Amount, TDS Amount and Disallowance Amount.")
            return False
        return True        
 
    def _validate_bill_status(self):
        if frappe.get_value('Bill', self.record['bill'], 'status') in ["CANCELLED", "CANCELLED AND DELETED"]:
            if self.record['advice']:
                Matcher.update_advice_status(self.record['advice'], 'Warning', 'Cancelled Bill')
            return False
        if frappe.get_value('Bill', self.record['bill'], 'status') == 'Paid':
            if self.record['advice']:
                Matcher.update_advice_status(self.record['advice'], 'Warning', 'Already Paid Bill')
            return False
        return True
 
    def _validate_bank_transaction(self):
        if self.record.get('bank', ''):
            if len(self.record['bank']) < 4:
                if self.record['advice']:
                    Matcher.update_advice_status(self.record['advice'], 'Warning', 'Reference number should be minimum of 5 digits')
                return False
 
            if int(frappe.get_value('Bank Transaction', self.record['bank'], 'deposit')) < 8:
                if self.record['advice']:
                    Matcher.update_advice_status(self.record['advice'], 'Warning', 'Deposit amount should be greater than 8')
                return False
 
            if frappe.get_value('Bank Transaction', self.record['bank'], 'status') == 'Reconciled':
                if self.record['advice']:
                    Matcher.update_advice_status(self.record['advice'], 'Warning', 'Already Reconciled')
                return False
        return True
 
class Matcher:
    def add_log_error(self, doctype, name, error):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype)
        error_log.set('reference_name', name[0:100])
        error_log.set('error_message', error[0:139])
        error_log.save()
 
    def update_payment_order(self, matcher_record, record):
        matcher_record.set("payment_order", record['payment_order'])
        return matcher_record
 
    def update_matcher_amount(self, matcher_record, record):
        matcher_record.set("claim_amount", record['claim_amount'])
        matcher_record.set("settled_amount", record['settled_amount'])
        matcher_record.set("tds_amount", record['tds_amount'])
        matcher_record.set('disallowance_amount', record['disallowed_amount'])
        return matcher_record
 
    def get_matcher_name(self, _prefix, _suffix):
        return f"{_prefix}-{_suffix}"
 
    @staticmethod
    def update_advice_status(sa_name, status, msg):
        advice_doc = frappe.get_doc('Settlement Advice', sa_name)
        advice_doc.status = status
        advice_doc.remark = msg
        advice_doc.save()
 
    def create_matcher_record(self, matcher_records, payment_logic):
        for record in matcher_records:
           
            if not MatcherValidation(record).is_valid():
                continue
            try  :
              matcher_record = frappe.new_doc("Matcher")
              matcher_record.set('sales_invoice', record['bill'])
              matcher_record = self.update_matcher_amount(matcher_record, record)
 
              if record['advice']:
                matcher_record.set('settlement_advice', record['advice'])
              if record['claim']:
                matcher_record.set('claimbook', record['claim'])
                matcher_record.set('insurance_company_name', record['insurance_name'])
              if record['logic'] in payment_logic:
                if record.payment_order:
                    matcher_record = self.update_payment_order(matcher_record, record)
              if record['bank']:
                matcher_record.set('bank_transaction', record['bank'])
                matcher_record.set('name', self.get_matcher_name(record['bill'], record['bank']))
              else:
                if record['claim']:
                    matcher_record.set('name', self.get_matcher_name(record['bill'], record['claim']))
                else:
                    matcher_record.set('name', self.get_matcher_name(record['bill'], record['advice']))
 
              matcher_record.set('match_logic', record['logic'])
              matcher_record.set('status', 'Open')
            except Exception as e:
                log_error(e)
 
            try:
                matcher_record.save()
                if record['advice']:
                    update_query = """
                        UPDATE `tabSettlement Advice`
                        SET status = %(status)s, matcher_id = %(matcher_id)s
                        WHERE name = %(name)s
                    """
                    frappe.db.sql(update_query, values={'status': 'Not Processed', 'matcher_id': matcher_record.name, 'name': matcher_record.settlement_advice})
                frappe.db.commit()
            except Exception as e:
                if record['advice']:
                    update_query = """
                        UPDATE `tabSettlement Advice`
                        SET status = %(status)s, remark = %(remark)s
                        WHERE name = %(name)s
                    """
                    frappe.db.sql(update_query, values={'status': 'Error', 'remark': str(e), 'name': matcher_record.settlement_advice})
                self.add_log_error('Matcher', matcher_record.name, str(e))      
 
    def preprocess_entries(self):
        match_logic = ('MA5-BN', 'MA3-CN', 'MA1-CN')
        frappe.db.sql("""Delete from `tabMatcher` where match_logic not in %(match_logic)s""" , values = {'match_logic' : match_logic})
        frappe.db.sql("""UPDATE `tabSettlement Advice` SET status = 'Open', remark = NULL, matcher_id = NULL WHERE status IN ('Unmatched', 'Open')""")
        update_bill_no_separate_column()
        frappe.db.commit()
   
    def postprocess_entries(self):
        update_query = """UPDATE `tabSettlement Advice` set status = 'Unmatched', remark = %(remark)s where status = 'Open'"""
        frappe.db.sql(update_query, values = { 'remark' : 'Not able to find Bill'})
        frappe.db.commit()
   
    def execute_cursors(self, match_logic, payment_logic):
        for logic_id in match_logic:
            records = frappe.db.sql(get_matcher_query(logic_id), as_dict=True)
            self.create_matcher_record(records, payment_logic)
        self.postprocess_entries()
       
    def process(self):
        match_logic, payment_logic = frappe.get_single("Control Panel").match_logic.split(","), frappe.get_single("Control Panel").payment_logic.split(",")
        update_index()
        self.preprocess_entries()
        self.execute_cursors(match_logic, payment_logic)
 
@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "InProgress")
        try:
            frappe.enqueue(Matcher().process
                           ,queue = 'long'
                           ,is_async = True
                           ,job_name = "Matcher_Process"
                           ,timeout = 25000)
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')