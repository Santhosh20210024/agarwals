import frappe
from agarwals.reconciliation import chunk
from agarwals.utils.error_handler import log_error
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.reconciliation.step.advice_downloader.provider_ihx_downloader import ProviderIhx
from agarwals.reconciliation.step.advice_downloader.tips_vidalhealthtpa import TipsVidalHealthTpa
from agarwals.reconciliation.step.advice_downloader.tnnhis_mdindia import TnnhisMdIndia
from agarwals.reconciliation.step.advice_downloader.star_health_downloader import StarHealthDownloader
from agarwals.reconciliation.step.advice_downloader.vitrya_downloader import VitryaDownloader
from agarwals.reconciliation.step.advice_downloader.health_india_downloader import HealthIndiaDownloader
from agarwals.reconciliation.step.advice_downloader.safeway_downloader import SafewayDownloader
from agarwals.reconciliation.step.advice_downloader.good_health import GoodHealthDownloader
from agarwals.reconciliation.step.advice_downloader.md_india import MDIndiaDownloader
from agarwals.reconciliation.step.advice_downloader.icici_lombard import ICICLombardDownloader
from agarwals.reconciliation.step.advice_downloader.star_vitraya import StarVitrayaDownloader
from agarwals.reconciliation.step.advice_downloader.vidalhealth_downloader import VidalHealthDownloader
from agarwals.reconciliation.step.advice_downloader.vidalhealth_downloader import VidalHealthDownloader
from agarwals.reconciliation.step.advice_downloader.bajaj_allianz import BajajAllianzDownloader
from agarwals.reconciliation.step.advice_downloader.paramount import ParamountDownloader
from agarwals.reconciliation.step.advice_downloader.care_health import CarehealthDownloader
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from agarwals.reconciliation.step.advice_downloader.fhpl import FHPLDownloader



def download_advice(tpa_doc, chunk_doc, args):
    class_name=eval(tpa_doc.executing_method)
    frappe.enqueue(class_name().download,queue = args["queue"], is_async = True, job_name = f"TPA_downloader_{str(tpa_doc.name)}", timeout = 3600, tpa_doc = tpa_doc, chunk_doc = chunk_doc)

@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        tpa_login_doc = frappe.get_all("TPA Login Credentials",fields='*',filters={'executing_method':args["executing_method"]})
        if tpa_login_doc:
            for tpa_login in tpa_login_doc:
                if tpa_login.is_enable == 1:
                    chunk_doc = chunk.create_chunk(args["step_id"])
                    download_advice(tpa_login, chunk_doc, args)
                else:
                    chunk_doc = chunk.create_chunk(args["step_id"])
                    chunk.update_status(chunk_doc, "Processed")
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')


@frappe.whitelist()
def download_captcha_settlement_advice(captcha_tpa_doc):
    login_ref_query = frappe.db.sql(
        f"SELECT tpa_login_credentials, name,idx FROM `tabSettlement Advice Downloader UI Logins` WHERE status = 'Open' AND parent = '{captcha_tpa_doc}' ORDER by idx ASC LIMIT 1",
        as_dict=True)
    try:
        if login_ref_query:
            login_ref = login_ref_query[0]
            doc_name = (login_ref.tpa_login_credentials)
            if doc_name:
                login = frappe.get_all('TPA Login Credentials', {'name': doc_name}, ['*'])[0]
                frappe.db.sql(
                    f"UPDATE `tabSettlement Advice Downloader UI Logins` SET status = 'InProgress' WHERE name = '{login_ref.name}' ")
                frappe.db.commit()
                target = eval(login.executing_method)
                target().download(tpa_doc=login, child=login_ref.name, parent=captcha_tpa_doc)
        else:
            frappe.msgprint(" No Login in Open Status ")
    except Exception as e:
        login_ref = login_ref_query[0]
        log_error(e, 'Settlement Advice Downloader UI', login_ref.name)
        if (frappe.db.sql(
                f"SELECT status FROM `tabSettlement Advice Downloader UI Logins` WHERE name = '{login_ref.name}'",
                as_dict=True)[0].status == "InProgress"):
            frappe.db.sql(
                f"UPDATE `tabSettlement Advice Downloader UI Logins` SET status = 'Error' WHERE name = '{login_ref.name}' ")
            frappe.db.commit()







