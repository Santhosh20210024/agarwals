import frappe
from agarwals.website_downloader.downloader import Mediassist

def enqueue_job(tpa_name,hospital_branch):
    frappe.enqueue(tpa_name(hospital_branch).download,queue='long', is_async=True, job_name="TPA_downloader", timeout=25000)