import frappe
from agarwals.website_downloader import downloader

@frappe.whitelist()
def enqueue_job(tpa_name,hospital_branch):
    class_name=getattr(downloader,tpa_name)
    frappe.enqueue(class_name(hospital_branch).download,queue='long', is_async=True, job_name="TPA_downloader", timeout=16000)