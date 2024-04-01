import frappe
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime,timedelta
import os
import shutil
from agarwals.utils.file_util import construct_file_url,SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR, HOME_PATH
# from agarwals.utils.path_data import SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR, HOME_PATH


class SeleniumDownloader:
    tpa=''
    branch_code=''
    last_executed_time=None
    def __init__(self):
        self.portal = None
        self.user_name = None
        self.password = None
        self.url = None
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.credential_doc=None
        self.files_path = SITE_PATH + "/private/files/DrAgarwals/"
        self.driver = None
        self.wait = None
        self.from_date = None
        self.to_date = None

    def set_username_password_and_password(self)  :
        self.credential_doc = frappe.db.get_list("TPA Login Credentials", filters={"branch_code":['=',self.branch_code],"tpa":['=',self.tpa]},fields="*")
        if self.credential_doc:
            self.user_name = self.credential_doc[0].user_name
            self.password = self.credential_doc[0].password
            self.url = self.credential_doc[0].url
            self.from_date = self.credential_doc[0].from_date
            self.to_date  = frappe.utils.now_datetime().date()
        else:
            self.log_error('TPA Login Credentials',None,"No Credential for the given input")

    def login(self):
        return None

    def navigate(self):
        return None

    def download_from_web(self):
        return None
    
    def insert_run_log(self, data):
        doc=frappe.get_doc("TPA Login Credentials",self.credential_doc[0].name)
        doc.append("run_log",data)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return None
    
    def create_directory(self, file_name):
        os.mkdir(self.files_path + file_name)
        return self.files_path + file_name

    def rename_downloaded_file(self, download_directory, file_name):
        original_file_name = os.listdir(download_directory)[0]
        extension = original_file_name.split(".")[-1]
        formatted_file_name = file_name + "." + extension
        os.rename(download_directory + '/' + original_file_name, download_directory + '/' + formatted_file_name)
        return formatted_file_name
        
    def move_file_to_extract(self, download_directory, formatted_file_name):
        shutil.move(download_directory + "/" + formatted_file_name, self.files_path + "Extract/" + formatted_file_name)

    def delete_folder(self,download_directory):
        shutil.rmtree(download_directory)

    def delete_backend_files(self,file_path=None):
        if os.path.exists(file_path):
            os.remove(file_path)

    def create_file_record(self, file_name):
        file = frappe.new_doc("File")
        file.folder = construct_file_url(HOME_PATH, SUB_DIR[0])
        file.is_private = 1
        file.file_url = "/" + construct_file_url(SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0], file_name)
        file.save(ignore_permissions=True)
        self.delete_backend_files(
            file_path=construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0], file_name))
        file_url = "/" + construct_file_url(SHELL_PATH, file_name)
        frappe.db.commit()
        return file_url
    
    def log_error(self,doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()
        if reference_name:
            self.insert_run_log({"last_executed_time":self.last_executed_time,"document_reference":"Error Record Log","reference_name":error_log.name,"status":"Error"})

    def create_fileupload(self,file_url,file_name):
        file_upload_doc=frappe.new_doc("File upload")
        file_upload_doc.document_type="Settlement Advice"
        file_upload_doc.payer_type=self.tpa
        file_upload_doc.upload=file_url
        file_upload_doc.save(ignore_permissions=True)
        self.insert_run_log({"last_executed_time":self.last_executed_time,"document_reference":"File upload","reference_name":file_upload_doc.name,"status":"Processed"})
        frappe.db.commit()

    
    def raise_exception(self,exception):
        raise Exception(exception)
    
    def download(self):
        try:
            self.set_username_password_and_password()
            file_name = f"{self.tpa.replace(' ','').lower()}_{self.user_name}_{self.branch_code}"
            download_directory = self.create_directory(file_name)
            prefs = {"download.default_directory": download_directory + "/"}
            self.options.add_experimental_option("prefs", prefs)
            self.driver = webdriver.Chrome(options=self.options)
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.get(self.url)
            self.login()
            self.navigate()
            self.download_from_web()
            if len(os.listdir(download_directory)) == 0 or len(os.listdir(download_directory)) > 1:
                self.raise_exception(f"Your directory {download_directory} has either no file or have multiple files")
            formatted_file_name = self.rename_downloaded_file(download_directory, file_name)
            self.move_file_to_extract(download_directory,formatted_file_name)
            self.delete_folder(download_directory)
            file_url = self.create_file_record(formatted_file_name)
            self.create_fileupload(file_url,file_name)
        except Exception as e:
            self.log_error('TPA Login Credentials',self.user_name,e)