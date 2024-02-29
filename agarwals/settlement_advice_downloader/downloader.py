import frappe
import requests
import json
import pandas as pd
import frappe
import shutil
import os
from agarwals.utils.file_util import construct_file_url
from agarwals.utils.path_data import PROJECT_FOLDER,HOME_PATH,SHELL_PATH,SUB_DIR,SITE_PATH

class Downloader():
    tpa=''
    branch_code=''
    def __init__(self):
            credential_doc = frappe.db.get_list("TPA Login Credentials", filters={"branch_code":['=',self.branch_code],"tpa":['=',self.tpa]},fields="*")
            if credential_doc:
                self.user_name = credential_doc[0].user_name
                self.password = credential_doc[0].password
            else:
                self.log_error('TPA Login Credentials',None,"No Credenntial for the given input")
        
    def delete_backend_files(self,file_path=None):
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def write_binary(self,file_name=None,content=None):
        if file_name and content:
            with open(file_name, "wb") as file:
                file.write(content)
            file_url=self.move_and_create_file_record(file_name)
            self.create_fileupload(file_url)
    
    def move_and_create_file_record(self,file_name):
        shutil.move(file_name,  construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0]))
        file=frappe.new_doc("File")
        file.folder = construct_file_url(HOME_PATH, SUB_DIR[0])
        file.is_private=1
        file.file_url= "/" + construct_file_url(SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0], file_name)
        file.save(ignore_permissions=True)
        self.delete_backend_files(file_path=construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0],file_name))
        file_url="/"+construct_file_url(SHELL_PATH, file_name)
        frappe.db.commit()
        return file_url
        
    def write_Json(self,file_name=None,content=None):
        if file_name and content:
            content_df=pd.DataFrame(content)
            content_df.to_excel(file_name)
            file_url=self.move_and_create_file_record(file_name)
            self.create_fileupload(file_url)
    
    def create_fileupload(self,file_url):
        file_upload_doc=frappe.new_doc("File upload")
        file_upload_doc.document_type="Settlement Advice"
        file_upload_doc.payer_type=self.tpa
        file_upload_doc.upload=file_url
        file_upload_doc.save(ignore_permissions=True)
        frappe.db.commit()

    def log_error(self,doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()
        
