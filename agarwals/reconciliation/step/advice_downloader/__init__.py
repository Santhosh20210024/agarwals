import frappe
from tfs.orchestration import ChunkOrchestrator, chunk
from agarwals.utils.error_handler import log_error
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.reconciliation.step.advice_downloader.bot_uploader import SABotUploader
from agarwals.reconciliation.step.advice_downloader.provider_ihx_api_downloader import ProviderIhx
from agarwals.reconciliation.step.advice_downloader.tips_vidal_health_downloader import TipsVidalHealth
from agarwals.reconciliation.step.advice_downloader.tnnhis_mdindia_downloader import TnnhisMdIndia
from agarwals.reconciliation.step.advice_downloader.star_health_downloader import StarHealthDownloader
from agarwals.reconciliation.step.advice_downloader.vitrya_downloader import VitryaDownloader
from agarwals.reconciliation.step.advice_downloader.health_india_downloader import HealthIndiaDownloader
from agarwals.reconciliation.step.advice_downloader.safeway_downloader import SafewayDownloader
from agarwals.reconciliation.step.advice_downloader.good_health_downloader import GoodHealthDownloader
from agarwals.reconciliation.step.advice_downloader.md_india_downloader import MDIndiaDownloader
from agarwals.reconciliation.step.advice_downloader.icici_lombard_downloader import ICICLombardDownloader
from agarwals.reconciliation.step.advice_downloader.star_vitraya_downloader import StarVitrayaDownloader
from agarwals.reconciliation.step.advice_downloader.vidalhealth_downloader import VidalHealthDownloader
from agarwals.reconciliation.step.advice_downloader.vidalhealth_downloader import VidalHealthDownloader
from agarwals.reconciliation.step.advice_downloader.bajaj_allianz_downloader import BajajAllianzDownloader
from agarwals.reconciliation.step.advice_downloader.paramount_downloader import ParamountDownloader
from agarwals.reconciliation.step.advice_downloader.care_health_downloader import CarehealthDownloader
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from agarwals.reconciliation.step.advice_downloader.fhpl_downloader import FHPLDownloader
from agarwals.reconciliation.step.advice_downloader.reliance_general_downloader import RelianceGeneralDownloader
from agarwals.reconciliation.step.advice_downloader.niva_bupa_downloader import NivaBupaDownloader
from agarwals.reconciliation.step.advice_downloader.provider_ihx_downoader import ProviderIhxDownloader
from agarwals.reconciliation.step.advice_downloader.eriscon_downloader import EricsonDownloader
from agarwals.reconciliation.step.advice_downloader.cmc_nethaji_downloader import CMCNethajiEyeFoundationDownloader
from agarwals.reconciliation.step.advice_downloader.cholas_downloader import CholasDownloader
from agarwals.reconciliation.step.advice_downloader.cmc_eyefoundation_downloader import CMCEyeFoundationDownloader
from agarwals.reconciliation.step.advice_downloader.cholas_pdf_downloader import CholasPdfDownloader
from agarwals.reconciliation.step.advice_downloader.heritage_downloder import HeritageDownloader


@ChunkOrchestrator.update_chunk_status
def download_advice(tpa_login_doc):
    chunk_status = "Processed"
    for tpa_doc in tpa_login_doc:
        class_name=eval(tpa_doc.executing_method)
        process_status = class_name().download(tpa_doc)
        chunk_status = chunk.get_status(chunk_status, process_status)
    return chunk_status

@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    if args.get("retry"):
        tpa_login_doc = frappe.db.sql("SELECT * FROM `tabTPA Login Credentials` WHERE retry = 1 AND is_enable = 1",as_dict=True)
    else:
        tpa_login_doc = frappe.db.sql(f"""SELECT * FROM `tabTPA Login Credentials` WHERE executing_method = '{args["executing_method"]}' AND status in ('New','Valid') AND is_enable = 1""",as_dict=True)
    ChunkOrchestrator().process(download_advice, step_id=args["step_id"], is_enqueueable=True, chunk_size=1, data_var_name="tpa_doc_list", queue=args["queue"],
                                is_async=True, timeout=3600, tpa_login_doc=tpa_doc_list)


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
                parent_doc = frappe.get_doc('Settlement Advice Downloader UI', captcha_tpa_doc)
                doc = frappe.get_doc("Settlement Advice Downloader UI Logins", login_ref.name)
                doc.update({
                    "status":"InProgress"
                })
                parent_doc.logins.append(doc)
                parent_doc.save(ignore_permissions = True)
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

@frappe.whitelist()
def upload_sa_files():
    SABotUploader().process()







