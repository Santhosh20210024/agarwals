import frappe
from agarwals.website_downloader import downloader

@frappe.whitelist(allow_guest=True)
def settlement_advice_job(tpa_name,hospital_branch):
    tpa_name=tpa_name.replace(" ","_")
    class_name=getattr(downloader,tpa_name)
    frappe.enqueue(class_name(hospital_branch).download,queue='long', is_async=True, job_name=f"TPA_downloader_{str(tpa_name)}_{hospital_branch}", timeout=3600)