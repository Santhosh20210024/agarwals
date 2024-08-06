import frappe
from tfs.profiler.timer import Timer
from frappe.utils.caching import redis_cache
from agarwals.utils.error_handler import log_error

def get_document_record(doctype, name):
    document_timer = Timer().start(f"get_document_record {doctype} - {name}")
    doc = frappe.get_doc(doctype, name)
    document_timer.end()
    return doc

def update_advice_log(advice, status, msg):
    advice_log_timer = Timer().start(f"update_advice_log {advice}")
    settlement_advice = get_document_record('Settlement Advice', advice)
    settlement_advice.status = status
    settlement_advice.remark = msg
    settlement_advice.save()
    advice_log_timer.end()

def update_matcher_log(matcher_record, status, msg):
    macher_log_timer = Timer().start(f"update_matcher_log {matcher_record.name}")
    matcher_record.status = status
    matcher_record.remarks = msg
    macher_log_timer.end()

def update_error(matcher_record, message, error=None):
    update_matcher_log(matcher_record.name, 'Error', message)
    if matcher_record.settlement_advice:
        update_advice_log(matcher_record.settlement_advice, 'Warning', message)
    if error:
        log_error(error, "Matcher", matcher_record.name)
    return None

@redis_cache
def get_company_account(bank_account_name):
    get_company_timer = Timer().start(f"get_company_account {bank_account_name}")
    bank_account = frappe.get_doc('Bank Account', bank_account_name)
    if not bank_account.account:
        get_company_timer.end()
        return None
    get_company_timer.end()
    return bank_account.account