from datetime import date, datetime
import frappe
from tfs.profiler.timer import Timer
from frappe.utils.caching import redis_cache
from frappe import utils
from frappe.model.document import Document
from agarwals.utils.error_handler import log_error


def get_document_record(doctype: str, name: str) -> "Document":
    document_timer = Timer().start(f"get_document_record {doctype} - {name}")
    doc: "Document" = frappe.get_doc(doctype, name)
    document_timer.end()
    return doc


def update_advice_log(advice: str, status: str, msg: str) -> None:
    advice_log_timer = Timer().start(f"update_advice_log {advice}")
    settlement_advice: "Document" = get_document_record('Settlement Advice', advice)
    settlement_advice.status = status
    settlement_advice.remark = msg
    settlement_advice.save()
    advice_log_timer.end()


def update_matcher_log(matcher_record: "Document", status: str, msg: str) -> None:
    macher_log_timer = Timer().start(f"update_matcher_log {matcher_record.name}")
    matcher_record.status = status
    matcher_record.remarks = msg
    macher_log_timer.end()


def update_error(matcher_record: "Document", message: str, error: str | Exception = None) -> None:
    update_matcher_log(matcher_record, 'Error', message)
    if matcher_record.settlement_advice:
        update_advice_log(matcher_record.settlement_advice, 'Warning', message)
    if error:
        log_error(error, "Matcher", matcher_record.name)


@redis_cache
def get_company_account(bank_account_name: str) -> str | None:
    get_company_timer = Timer().start(f"get_company_account {bank_account_name}")
    bank_account: "Document" = frappe.get_doc('Bank Account', bank_account_name)
    if not bank_account.account:
        get_company_timer.end()
        return None
    get_company_timer.end()
    return bank_account.account


@redis_cache
def get_entity_closing_date(entity: str) -> date | None:
    get_posting_date_timer = Timer().start(f"get_posting_date {entity}")
    closing_date_list = frappe.get_list('Period Closure by Entity',
                                        filters={'entity': entity}
                                        , order_by='creation desc'
                                        , pluck='posting_date')
    closing_date = max(closing_date_list) if closing_date_list else None
    get_posting_date_timer.end()
    return closing_date


@redis_cache
def get_posting_date(bt_date: date, entity_closing_date: date | None) -> date:
    if entity_closing_date and bt_date < entity_closing_date:
        return datetime.strptime(utils.today(), "%Y-%m-%d")
    return bt_date
