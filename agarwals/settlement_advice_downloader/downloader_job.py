import frappe
from datetime import datetime,timedelta
from agarwals import settlement_advice_downloader

def settlement_advice_job(tpa_name,branch_code,executing_method):
    class_name=getattr(settlement_advice_downloader,executing_method)
    class_name(tpa_name,branch_code).download()
    frappe.enqueue(class_name(branch_code).download,queue='long', is_async=True, job_name=f"TPA_downloader_{str(tpa_name)}_{branch_code}", timeout=3600)

@frappe.whitelist(allow_guest=True)
def execute_download_job():    
    tpa_credential_doc=frappe.get_all("TPA Login Credentials",fields='*')
    time_exc=datetime.now()
    for tpa_credential in tpa_credential_doc:
        if tpa_credential.exectution_time:
            if (time_exc-timedelta(minutes=1)).time()<tpa_credential.exectution_time.time()<=time_exc.time():
                settlement_advice_job(tpa_credential.tpa,tpa_credential.branch_code,tpa_credential.executing_method)