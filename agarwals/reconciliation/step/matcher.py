import frappe
from agarwals.utils.updater import update_bill_no_separate_column, update_utr_in_separate_column
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from agarwals.utils.index_update import update_index
from agarwals.utils.matcher_query_list import get_matcher_query

class Matcher:
    def add_log_error(self, doctype, name, error):
        log_name = name[0:100] 
        log_error = error[0:139] # Long Text fields only allows 140 Characters
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name',doctype)
        error_log.set('reference_name', log_name)
        error_log.set('error_message', log_error)
        error_log.save()
       
    def update_payment_order(self, matcher_record, record):  # Payment Order Used While Doing Payment Entry Process
        matcher_record.set("payment_order", record['payment_order'])
        return matcher_record

    def update_matcher_amount(self, matcher_record, record):
        matcher_record.set("settled_amount", record['settled_amount'])
        matcher_record.set("tds_amount", record['tds_amount'])
        matcher_record.set('disallowance_amount',record['disallowed_amount'])
        return matcher_record

    def get_matcher_name(self, _prefix, _suffix):  # i.e BankUTR-BillNO
        return _prefix + "-" + _suffix

    def update_advice_status(self, sa_name, status, msg):
        advice_doc = frappe.get_doc('Settlement Advice', sa_name)
        advice_doc.status = status
        advice_doc.remark = msg
        advice_doc.save()
        
    def validate_record(self, record):
        if record['advice']:  # Extra Validation
            if record.status not in ('Open', 'Not Processed'):
                return False
            
        claim_amount = float(record.claim_amount)
        settled_amount = float(record.settled_amount)
        tds_amount = float(record.tds_amount)
        disallowed_amount = float(record.disallowed_amount)
        
        if record['advice'] and claim_amount and settled_amount:
            if round(claim_amount) < round(settled_amount + tds_amount + disallowed_amount):
                self.update_advice_status(record['advice'], 'Warning', 'Claim Amount is greater than the cumulative of settled, tds and disallowance')
                return False
        
        if frappe.get_value('Bill', record['bill'], 'status') in ["CANCELLED", "CANCELLED AND DELETED"] :
            if record['advice']: 
                self.update_advice_status(record['advice'], 'Warning', 'Cancelled Bill')
            return False
        
        return True

    def create_matcher_record(self, matcher_records, payment_logic):
        if not len(matcher_records):
            return
        
        for record in matcher_records:
            if not self.validate_record(record):
                continue
            
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
            
            try:
                matcher_record.save()
                if record['advice']:
                    update_query = """
                                    UPDATE `tabSettlement Advice`
                                    SET status = %(status)s, matcher_id = %(matcher_id)s
                                    WHERE name = %(name)s
                                """
                    frappe.db.sql(update_query, values = { 'status' : 'Not Processed', 'matcher_id' : matcher_record.name, 'name': matcher_record.settlement_advice})
                frappe.db.commit()
            except Exception as e:
                if record['advice']:
                    update_query = """
                                        UPDATE `tabSettlement Advice`
                                        SET status = %(status)s, remark = %(remark)s
                                        WHERE name = %(name)s
                                    """
                    frappe.db.sql(update_query, values = { 'status' : 'Error', 'remark' : str(e), 'name': matcher_record.settlement_advice})
                self.add_log_error('Matcher', matcher_record.name, str(e))
                

    def preprocess_entries(self):
        match_logic = ('MA5-BN', 'MA3-CN', 'MA1-CN') 
        frappe.db.sql("""Delete from `tabMatcher` where match_logic not in %(match_logic)s""" , values = {'match_logic' : match_logic})
        frappe.db.sql("""Update `tabSettlement Advice` SET status = 'Open', remark = NULL, matcher_id = NULL  where status in ('Not Processed', 'Open')""")
        frappe.db.sql("""Update `tabSettlement Advice` SET status = ' remark = NULL, matcher_id = NULL where remark in ( 'Not able to find Bill')""")
        update_bill_no_separate_column()
        frappe.db.commit()
    
    def postprocess_entries(self):
        update_query = """UPDATE `tabSettlement Advice` set status = 'Warning', remark = %(remark)s where status = 'Open'"""
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
            frappe.enqueue(Matcher().process()
                           ,queue = 'long'
                           ,is_async = True
                           ,job_name = "Matcher_Process"
                           ,timeout = 25000)
            
            # Enqueue Operation Change
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')