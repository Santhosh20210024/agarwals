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
from agarwals.utils.file_util import construct_file_url
from agarwals.utils.path_data import SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR, HOME_PATH


class SeleniumDownloader:
    def __init__(self):
        self.portal = None
        self.user_name = None
        self.password = None
        self.url = None
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.files_path = SITE_PATH + "/private/files/DrAgarwals/"
        self.driver = None
        self.wait = None

    def get_credential_and_file_name(self):
        tpa_credential_doc = frappe.get_list("TPA Login Credentials",
                                             filters={'portal': self.portal, 'method': 'Selenium'}, fields='*')
        time_exc = datetime.now()
        for tpa_credential in tpa_credential_doc:
            if tpa_credential.exectution_time:
                if (time_exc - timedelta(minutes=5)).time() < tpa_credential.exectution_time.time() <= time_exc.time():
                    return {"user_name": tpa_credential['user_name'], "password": tpa_credential['password']}, tpa_credential['tpa'] + "-" + tpa_credential['branch_code']
        return {}, None

    def set_username_and_password(self, credentials):
        self.user_name = credentials['user_name']
        self.password = credentials['password']

    def login(self):
        return None

    def navigate(self):
        return None

    def download(self):
        return False

    def create_directory(self, file_name):
        try:
            os.mkdir(self.files_path + file_name)
            print(self.files_path + file_name)
            return self.files_path + file_name
        except:
            return None

    def rename_downloaded_file(self, download_directory, file_name):
        try:
            original_file_name = os.listdir(download_directory)[0]
            extension = original_file_name.split(".")[-1]
            formatted_file_name = file_name + "." + extension
            os.rename(download_directory + '/' + original_file_name, download_directory + '/' + formatted_file_name)
            return formatted_file_name
        except Exception as e:
            print("1", e)
            return None

    def move_file_to_extract(self, download_directory, formatted_file_name):
        try:
            shutil.move(download_directory + "/" + formatted_file_name, self.files_path + "Extract/" + formatted_file_name)
            return True
        except Exception as e:
            print("2", e)
            return False

    def delete_folder(self,download_directory):
        shutil.rmtree(download_directory)

    def delete_backend_files(self,file_path=None):
        if os.path.exists(file_path):
            os.remove(file_path)

    def create_file_record(self, file_name):
        try:
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
        except Exception as e:
            print("3",e)
            return None

    def create_fileupload(self,file_url,file_name):
        file_upload_doc=frappe.new_doc("File upload")
        file_upload_doc.document_type="Settlement Advice"
        file_upload_doc.payer_type=file_name.split('-')[0]
        file_upload_doc.upload=file_url
        file_upload_doc.save(ignore_permissions=True)
        frappe.db.commit()


    def process(self):
        print(SITE_PATH)
        credentials, file_name = self.get_credential_and_file_name()
        download_directory = self.create_directory(file_name)
        if not download_directory:
            return
        prefs = {"download.default_directory": download_directory + "/"}
        self.options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        if not credentials:
            return
        self.set_username_and_password(credentials)
        self.driver.get(self.url)
        self.login()
        self.navigate()
        downloaded = self.download()
        if not downloaded:
            return
        if len(os.listdir(download_directory)) == 0 and len(os.listdir(download_directory)) > 1:
            return
        formatted_file_name = self.rename_downloaded_file(download_directory, file_name)
        if not formatted_file_name:
            return
        file_moved = self.move_file_to_extract(download_directory,formatted_file_name)
        if not file_moved:
            return
        self.delete_folder(download_directory)
        file_url = self.create_file_record(formatted_file_name)
        if not file_url:
            return
        self.create_fileupload(file_url,file_name)