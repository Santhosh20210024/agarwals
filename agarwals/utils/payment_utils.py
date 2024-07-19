import frappe
from tfs.profiler.timer import Timer
from frappe.utils.caching import redis_cache

def update_advice_log(advice, status, msg):
    advice_log_timer = Timer().start(f"update_advice_log {advice}")
    frappe.db.set_value('Settlement Advice', advice, 'status', status)
    frappe.db.set_value('Settlement Advice', advice, 'remark', msg)
    advice_log_timer.end()

def update_matcher_log(name, status, msg):
    macher_log_timer = Timer().start(f"update_matcher_log {name}")
    frappe.db.set_value('Matcher', name, 'status', status)
    frappe.db.set_value('Matcher', name, 'remarks', msg)
    macher_log_timer.end()

def update_error(matcher_record, message):
    update_matcher_log(matcher_record.name, 'Error', message)
    if matcher_record.settlement_advice:
        update_advice_log(matcher_record.settlement_advice, 'Warning', message)
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