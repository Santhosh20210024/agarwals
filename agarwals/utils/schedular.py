import frappe
from datetime import datetime,timedelta
from agarwals.utils.run_transform import run_transform_process
from agarwals.utils.settlement_advice import advice_transform
from agarwals.utils.sales_invoice_creator import create_sales_invoice
from agarwals.utils.insurance_mapping import tag_insurance_pattern
from agarwals.utils.bank_transaction_process import process as bk_process
from agarwals.utils.claim_key_mapper import map_claim_key
from agarwals.utils.payment_entry_creator import run_payment_entry
from agarwals.utils.matcher import update_matcher
from agarwals.utils.settlement_advice_staging_process import process as sa_process
from agarwals.settlement_advice_downloader.downloader_job import execute_download_job
@frappe.whitelist()
def execute_schedule_job():
    step_doc=frappe.get_all("Step",fields='*')
    schedule = frappe.get_doc('Scheduled Job Type',"downloader_job.execute_schedule_job",fields="*")
    time_exc=schedule.next_execution - timedelta(minutes=5)
    for step in step_doc:
        if step.type == "bill_transform" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                run_transform_process("debtors")
        if step.type == "sale_invoice_creation" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                create_sales_invoice("debtors")
        if step.type == "claimbook_transform" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                run_transform_process("claimbook")
        if step.type == "sa_transform" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                advice_transform()
        if step.type == "sa_staging" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                sa_process()
        if step.type == "ba_transform" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                run_transform_process("transaction")
        if step.type == "insurance_tagging" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                tag_insurance_pattern("Bank Transaction Staging")
        if step.type == "ba_staging" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                bk_process("Insurance")
        if step.type == "claim_key" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                map_claim_key()
        if step.type == "update_matcher" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                update_matcher()
        if step.type == "payment_entry" and step.time:
            if (time_exc-timedelta(minutes=5)).time()<step.time.time()<=time_exc.time():
                run_payment_entry()