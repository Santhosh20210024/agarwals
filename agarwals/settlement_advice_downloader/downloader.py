import frappe
import requests
import json
import frappe
import shutil
import os
from datetime import datetime,timedelta,date
from agarwals.utils.file_util import construct_file_url
from agarwals.utils.path_data import PROJECT_FOLDER,HOME_PATH,SHELL_PATH,SUB_DIR


class Downloader:

    def __init__(self):
        self.user_name = None
        self.password = None
        self.portal = None
        self.SITE_PATH = "/home/balamurugan/agarwals-bench-2/sites/sa-downloader"

    def log_error(self,doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()

    def get_user_credentials_tpa_and_branch(self):
        tpa_credential_doc = frappe.get_list("TPA Login Credentials",filters={'portal':self.portal}, fields='*')
        time_exc = datetime.now()
        for tpa_credential in tpa_credential_doc:
            if tpa_credential.exectution_time:
                if (time_exc - timedelta(minutes=2)).time() < tpa_credential.exectution_time.time() <= time_exc.time():
                    return tpa_credential['branch_code'], tpa_credential['tpa'], tpa_credential['user_name'], tpa_credential['password']
        return None, None, None, None

    def delete_backend_files(self,file_path=None):
        if os.path.exists(file_path):
            os.remove(file_path)

    def write_to_file(self, file_name, content, tpa):
        if file_name and content:
            with open(file_name, "wb") as file:
                file.write(content)
            shutil.move(file_name,
                        construct_file_url(self.SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0]))
            file = frappe.new_doc("File")
            file.folder = construct_file_url(HOME_PATH, SUB_DIR[0])
            file.is_private = 1
            file.file_url = "/" + construct_file_url(SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0],
                                                     file_name)
            file.save(ignore_permissions=True)
            self.delete_backend_files(
                file_path=construct_file_url(self.SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0],
                                             file_name))
            file_url = "/" + construct_file_url(SHELL_PATH, file_name)
            frappe.db.commit()
            self.create_fileupload(file_url, tpa)


    def get_content(self):
        return None

    def create_fileupload(self,file_url, tpa):
        file_upload_doc=frappe.new_doc("File upload")
        file_upload_doc.document_type="Settlement Advice"
        file_upload_doc.payer_type=tpa
        file_upload_doc.upload=file_url
        file_upload_doc.save(ignore_permissions=True)
        frappe.db.commit()

    def process(self):
        branch_name, tpa, self.user_name, self.password = self.get_user_credentials_tpa_and_branch()
        if not self.password:
            self.log_error('TPA Login Credentials', self.user_name, error_message=f"No Credential found for {self.user_name}")
            return
        content = self.get_content()
        if not content:
            if not branch_name and not tpa:
                self.log_error('TPA Login Credentials', self.user_name,
                               error_message=f"Branch Name or TPA Name not found for {self.user_name}")
                return
        file_name = f"{tpa.replace(' ','').lower()}_{self.portal}_{branch_name}.xlsx"
        self.write_to_file(file_name,content,tpa)
