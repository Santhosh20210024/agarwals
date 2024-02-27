import frappe
from datetime import datetime,timedelta
from agarwals.website_downloader import downloader


def settlement_advice_job(tpa_name,hospital_branch):
    tpa_name=tpa_name.replace(" ","_")
    class_name=getattr(downloader,tpa_name)
    frappe.enqueue(class_name(hospital_branch).download,queue='long', is_async=True, job_name=f"TPA_downloader_{str(tpa_name)}_{hospital_branch}", timeout=3600)

@frappe.whitelist(allow_guest=True)
def execute_download_job():    
    tpa_credential_doc=frappe.get_all("TPA Login Credentials",fields='*')
    time_exc=datetime.now()
    print((time_exc-timedelta(minutes=5)).time())
    for tpa_credential in tpa_credential_doc:
        if tpa_credential.exectution_time:
            if (time_exc-timedelta(minutes=5)).time()<tpa_credential.exectution_time.time()<=time_exc.time():
                settlement_advice_job(tpa_credential.tpa,tpa_credential.hospital_branch)