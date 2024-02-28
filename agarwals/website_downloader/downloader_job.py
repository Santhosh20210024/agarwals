import frappe
from datetime import datetime,timedelta
from agarwals.website_downloader import downloader


def settlement_advice_job(tpa_name,branch_code):
    tpa_name=tpa_name.replace(" ","_")
    class_name=getattr(downloader,tpa_name)
    frappe.enqueue(class_name(branch_code).download,queue='long', is_async=True, job_name=f"TPA_downloader_{str(tpa_name)}_{branch_code}", timeout=3600)

@frappe.whitelist(allow_guest=True)
def execute_download_job():    
    tpa_credential_doc=frappe.get_all("TPA Login Credentials",fields='*')
    time_exc=datetime.now()
    for tpa_credential in tpa_credential_doc:
        if tpa_credential.exectution_time:
            if (time_exc-timedelta(minutes=1)).time()<tpa_credential.exectution_time.time()<=time_exc.time():
                settlement_advice_job(tpa_credential.tpa,tpa_credential.branch_code)