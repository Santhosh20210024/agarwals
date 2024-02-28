import frappe
import requests
import json
import frappe
import shutil
import os
from agarwals.utils.file_util import construct_file_url

class Downloader:
    def __init__(self):
        self.tpa = None
        self.branch_name = None
        self.user_name = None
        self.password = None

    def log_error(self,doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()

    def get_user_credentials(self, tpa, branch):
        credential_doc = frappe.db.get_list("TPA Login Credentials",
                                            filters={"branch_code": ['=', self.branch_code], "tpa": ['=', self.tpa]},
                                            fields="*")
        if not credential_doc:
            return None, None

    def write_to_file(self, file_name, content):
        return


    def get_content(self, username, password):
        return None

    def create_fileupload(self,file_url):
        file_upload_doc=frappe.new_doc("File upload")
        file_upload_doc.document_type="Settlement Advice"
        file_upload_doc.payer_type=self.tpa
        file_upload_doc.upload=file_url
        file_upload_doc.save(ignore_permissions=True)
        frappe.db.commit()

    def process(self):
        self.user_name, self.password = self.get_user_credentials(self.tpa, self.branch_name)
        if not self.user_name:
            self.log_error('TPA Login Credentials', error_message="No Credenntial for the given input")
            return
        content = self.get_content(self.user_name, self.password)
        file_name = f"{self.tpa}_{self.branch_code}.xlsx"
        if not content:
            return
        self.write_to_file(file_name,content)

