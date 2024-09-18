import frappe
from agarwals.reconciliation.job.job_processor import JobProcessor
from typing import List

@frappe.whitelist()
def run(job_config):
    runner=JobProcessor()
    runner.start(job_config)

def latest_job_name(type:str="Reconciliation",status:str='InProgress') -> str | None:
    job_name: List = frappe.db.sql(f"""SELECT name FROM `tabJob` WHERE job_type = '{type}' AND status = '{status}' ORDER BY creation DESC LIMIT 1""",pluck='name')
    if job_name:
        return job_name[0]
    else:
        return None
