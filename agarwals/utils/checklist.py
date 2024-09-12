import frappe
from agarwals.utils.error_handler import log_error
from datetime import datetime, timedelta
import pandas as pd
from agarwals.reconciliation import chunk
import os
from agarwals.utils.str_to_dict import cast_to_dic
from typing import List
control_panel = frappe.get_doc("Control Panel")
site_path = control_panel.site_path
project_folder = control_panel.project_folder
class Checker:
    test_cases = {
        'S01': 'Evaluation of claim amounts in sales invoices',
        'S02': 'Evaluation of outstanding amounts and their status in sales invoices',
        'P01': 'Evaluation of total allocated amount in payment entries',
        'P02': 'Evaluation of whether the allocated amount in the bank transaction matches the paid amount in the payment entry',
        'B01': 'Evaluation of the presence of the party and party type in bank transactions',
        'B02': 'Evaluation of unallocated amounts in bank transactions',
        'B03': 'Evaluation of  bank transactions staging processed records with bank transactions',
        'SA01': 'Evaluation of settlement advice staging and settlement advice',
        'M01': 'Evaluation of matcher records with status equal to "Open" after the matching process',
        'U01': 'Evaluation of the presence of UTR Key in bank transactions',
        'U02': 'Evaluation of the presence of UTR Key in settlement advice',
        'U03': 'Evaluation of the presence of UTR Key in the claim book',
        'C01': 'Evaluation of presence of claim key in Bill',
        'C02': 'Evaluation of the presence of claim key in settlement advice',
        'C03': 'Evaluation of the presence of claim key in Claim Book',
        'BA01': 'Evaluation of all processed bill adjustments has been recorded with a journal entry'
    }

    def load_configurations(self):
        self.control_panel:object = frappe.get_doc("Control Panel")
        self.site_path:str = control_panel.site_path or self.raise_exception("Site path Not Found")
        self.project_folder:str = control_panel.project_name or self.raise_exception("Project Folder Name not Found")
        self.mail_group:str =  control_panel.check_list_mail_group or self.raise_exception("No mail group Found")

    def raise_exception(self, msg: str) -> None:
        raise Exception(msg)

    def is_exits(self,doctype:str) -> bool:
        count = len(frappe.get_list("File Records",{"reference_doc":doctype,"job":self.job_id}))
        return True if count > 0 else False

    def cy_sales_invoice_report(self):
        if self.is_exits(doctype="Payment Entry"):
            total_claim_amount = """SELECT SUM(vsir.`Claim Amount`),(SUM(vsir.`Total Settled Amount`)+ SUM(vsir.`Total TDS Amount`) + SUM(vsir.`Total Disallowance Amount`) ) as total_paid from
                                    `viewSales Invoice Report 24-25` `vsir`;"""
        else:
            log_error(error=f"Payment Entry not Found for the job {self.job_id}- Checklist",status="INFO")
            frappe.set_value()
    def check_reports(self):
        self.cy_sales_invoice_report()


    def process(self,chunk_doc) -> None:
        try:
            self.job_id = chunk_doc.job_id
            if self.job_id:
                self.load_configurations()
                self.check_reports()
            else:
                self.raise_exception("No Job ID Found to create checkList")
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")
            log_error(error=e,doc_name="Check List")


@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    chunk_doc = chunk.create_chunk(args["step_id"])
    try:
        checklist_instance = Checker()
        frappe.enqueue(checklist_instance.process, queue='long', job_name=f"checklist - {frappe.utils.now_datetime()}",chunk=chunk_doc)
    except Exception as e:
        chunk.update_status(chunk_doc, "Error")
        log_error(f"error While Processing checklist - {e}")

@frappe.whitelist()
def delete_checklist():
    try:
        path = frappe.get_single("Control Panel").site_path + f"/private/files/{PROJECT_FOLDER}/CheckList/"
        if os.path.exists(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        log_error(f"Error deleting file {file_path}: {e}")
        else:
            log_error("Path Not exits")
    except Exception as e:
        log_error(f"Error deleting checklist - {e}")