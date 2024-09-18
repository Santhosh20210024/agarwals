import frappe
from agarwals.reconciliation.job.job_processor import JobProcessor

@frappe.whitelist()
def run(job_config):
    runner=JobProcessor()
    runner.start(job_config)