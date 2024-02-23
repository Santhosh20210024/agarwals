import frappe
from agarwals.website_downloader.downloader import Mediassit

def enqueue_job(tpa_name,branch_name):
    frappe.enqueue(Mediassit().download,queue='long', is_async=True, job_name="TPA_downloader", timeout=25000,tpa_name=tpa_name,branch_name=branch_name)