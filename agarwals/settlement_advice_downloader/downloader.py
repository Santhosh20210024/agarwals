import frappe
import pandas as pd
import frappe
import shutil
import os
from agarwals.utils.file_util import construct_file_url

class Downloader():
    tpa=''
    branch_code=''
    last_executed_time=None
    def __init__(self):
        self.user_name = None
        self.password = None        
        self.PROJECT_FOLDER = "DrAgarwals"
        self.HOME_PATH = "Home/DrAgarwals"
        self.SHELL_PATH = "private/files"
        self.SUB_DIR = ["Extract", "Transform", "Load", "Bin"]
        self.SITE_PATH=frappe.get_single("Control Panel").site_path
        self.is_binary=False
        self.is_json=False
        self.credential_doc=None
        
    def set_username_and_password(self)  :
        self.credential_doc = frappe.db.get_list("TPA Login Credentials", filters={"branch_code":['=',self.branch_code],"tpa":['=',self.tpa]},fields="*")
        if self.credential_doc:
            self.user_name = self.credential_doc[0].user_name
            self.password = self.credential_doc[0].password
        else:
            self.log_error('TPA Login Credentials',None,"No Credential for the given input")
            
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
        shutil.move(file_name,  construct_file_url(self.SITE_PATH, self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0]))
        file=frappe.new_doc("File")
        file.folder = construct_file_url(self.HOME_PATH, self.SUB_DIR[0])
        file.is_private=1
        file.file_url= "/" + construct_file_url(self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0], file_name)
        file.save(ignore_permissions=True)
        self.delete_backend_files(file_path=construct_file_url(self.SITE_PATH, self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0],file_name))
        file_url="/"+construct_file_url(self.SHELL_PATH, file_name)
        frappe.db.commit()
        return file_url
     
    def insert_run_log(self, data):
        doc=frappe.get_doc("TPA Login Credentials",self.credential_doc[0].name)
        doc.append("run_log",data)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return None
    
    def write_json(self,file_name=None,content=None):
        if file_name and content:
            content_df=pd.DataFrame(content)
            content_df.to_excel(file_name)
            file_url=self.move_and_create_file_record(file_name)
            self.create_fileupload(file_url)
    
    def create_fileupload(self,file_url):
        file_upload_doc=frappe.new_doc("File upload")
        file_upload_doc.document_type="Settlement Advice"
        file_upload_doc.payer_type=self.tpa
        file_upload_doc.is_bot = 1
        file_upload_doc.upload=file_url
        file_upload_doc.save(ignore_permissions=True)
        self.insert_run_log({"last_executed_time":self.last_executed_time,"document_reference":"File upload","reference_name":file_upload_doc.name,"status":"Processed"})
        frappe.db.commit()

    def log_error(self,doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()
        if reference_name:
            self.insert_run_log({"last_executed_time":self.last_executed_time,"document_reference":"Error Record Log","reference_name":error_log.name,"status":"Error"})

    def get_content():
        return None
    
    def get_file_details(self):
        file_name = f"{self.tpa.replace(' ','').lower()}_{self.user_name}_{self.branch_code}.xlsx"
        self.is_binary=True
        return file_name
    
    def write_file(self,file_name,content):
        if self.is_binary:
            self.write_binary(file_name,content)
        if self.is_json:
            self.write_json(file_name,content)
    
    def get_meta_data(self, class_name, type, replace_dict):
        meta_data_doc=frappe.get_doc("Login Meta Data Configuration",f"{class_name}-{type}", fields="*")
        url=meta_data_doc.url
        body=meta_data_doc.body
        header=meta_data_doc.header
        params=meta_data_doc.params
        cookies=meta_data_doc.cookies 
        for key in replace_dict.keys():
            for value_dict in replace_dict[key]:
                if key=="header":
                    header=header.replace(list(value_dict.keys())[0], str(list(value_dict.values())[0]))
                if key=="body":
                    body=body.replace(list(value_dict.keys())[0], str(list(value_dict.values())[0]))
                if key=="params":
                    params=params.replace(list(value_dict.keys())[0], str(list(value_dict.values())[0]))
                if key=="cookie":
                    cookies=cookies.replace(list(value_dict.keys())[0], str(list(value_dict.values())[0]))
        if params:
            params=eval(params)
        if body:
            body=eval(body)
        if cookies:
            cookies=eval(cookies)
        return url, eval(header), body, params, cookies
        
    def download(self):
        try:
            self.set_username_and_password()
            content = self.get_content()
            file_name=self.get_file_details()
            if not content and not file_name:
                self.log_error('TPA Login Credentials', self.user_name, "No Data")
            self.write_file(file_name=file_name,content=content)
        except Exception as e:
            self.log_error('TPA Login Credentials',self.user_name,e)