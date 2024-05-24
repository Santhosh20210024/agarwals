import frappe
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime,timedelta
from html2excel import ExcelParser
import os
import shutil
from agarwals.reconciliation import chunk
from PIL import Image
import os
import shutil
import pandas as pd
import openpyxl

class SeleniumDownloader:
    def __init__(self):
        self.file_name = ''
        self.user_name = None
        self.password = None
        self.url = None
        self.options = webdriver.ChromeOptions()
        self.credential_doc=None
        self.PROJECT_FOLDER = "DrAgarwals"
        self.HOME_PATH = "Home/DrAgarwals"
        self.SHELL_PATH = "private/files"
        self.SUB_DIR = ["Extract", "Transform", "Load", "Bin"]
        self.SITE_PATH=frappe.get_single("Control Panel").site_path
        self.files_path = self.SITE_PATH + "/private/files/DrAgarwals/"
        self.driver = None
        self.wait = None
        self.from_date = None
        self.to_date = None
        self.download_directory = ''
        self.last_executed_time = frappe.utils.now_datetime()
        self.public_path = "public/files"
        self.child_reference_name = ''
        self.captcha_tpa_doc = ''
        self.full_img_path = ''
        self.crop_img_path = ''
        self.captcha_img_name = ''
        self.executing_child_class = ''
        self.tpa = ''
        self.is_captcha = False
        self.is_headless = True
        self.incoming_file_type = ''
        self.max_wait_time = 0

    def construct_file_url(*args):
        list_of_items = []
        for arg in args:
            if type(arg)==str:
                list_of_items.append(arg)
        formatted_url = '/'.join(list_of_items)
        return formatted_url



    def set_self_variables(self, tpa_doc ,child = None, parent = None):
        self.credential_doc = tpa_doc
        if self.credential_doc:
            self.user_name = self.credential_doc.user_name
            self.password = self.credential_doc.password
            self.executing_child_class = self.credential_doc.executing_method
            self.to_date = frappe.utils.now_datetime().date()
            if frappe.db.exists("SA Downloader Configuration",{"name":self.executing_child_class}):
                configuration_values = frappe.db.sql(f"SELECT * FROM `tabSA Downloader Configuration` WHERE `name`='{self.executing_child_class}'",as_dict=True)[0]
                self.is_captcha = True if configuration_values.is_captcha == 1 else False
                self.is_headless = True if configuration_values.is_headless == 1 else False
                self.incoming_file_type = configuration_values.incoming_file_type
                self.max_wait_time = configuration_values.captcha_entry_duration
                self.url = configuration_values.website_url
                self.from_date = configuration_values.from_date
            else:
                self.raise_exception(" SA Downloader Configuration not found ")
            if child and parent is not None:
                self.child_reference_name = child
                self.captcha_tpa_doc = parent
                self.tpa = self.credential_doc.name
        else:
            self.log_error('TPA Login Credentials',None,"No Credential for the given input")

    def get_captcha_value(self):
        try:
            captcha = ''
            end_time = time.time() + self.max_wait_time
            while time.time() < end_time:
                frappe.db.commit()
                captcha_value = frappe.db.sql(f"SELECT captcha FROM `tabSettlement Advice Downloader UI` WHERE name = '{self.captcha_tpa_doc}'",as_dict = True)
                if captcha_value[0].captcha:
                    captcha = captcha_value[0].captcha
                    break
            return captcha if captcha !='' else None
        except Exception as E:
            self.log_error('Settlement Advice Downloader UI',self.tpa, E)

    def extract_table_data(self, table_id):
        table = self.wait.until(EC.presence_of_element_located((By.ID, table_id)))
        table_html = table.get_attribute('outerHTML')
        with open(f'{self.download_directory}/{self.tpa}.html', 'w') as file:
            file.write(table_html)

    def attach_captcha_img(self,file_url=None):
        captcha_reference_doc = frappe.get_doc('Settlement Advice Downloader UI',self.captcha_tpa_doc)
        captcha_reference_doc.captcha_img =  file_url
        captcha_reference_doc.captcha = ''
        captcha_reference_doc.save()
        frappe.db.commit()
        captcha_reference_doc.reload()

    def create_captcha_file(self):
        file_doc = frappe.new_doc("File")
        file_doc.file_name = f"{self.tpa}_{frappe.utils.now_datetime()}captcha.png"
        file_doc.is_private = 1
        file_doc.file_url = "/" + self.construct_file_url(self.SHELL_PATH,f"{self.tpa}_captcha.png")
        file_doc.attached_to_doctype = "Settlement Advice Downloader UI"
        file_doc.attached_to_name = self.captcha_tpa_doc
        file_doc.attached_to_field = 'captcha_img'
        file_doc.save()
        frappe.db.commit()
        self.captcha_img_name = file_doc.name
        self.attach_captcha_img(file_doc.file_url)

    def delete_captcha_images(self):
        if self.full_img_path and self.crop_img_path:
            self.delete_backend_files(self.full_img_path)
            self.delete_backend_files(self.crop_img_path)
            file_url = frappe.db.sql(f"SELECT file_url FROM tabFile WHERE attached_to_name = '{self.captcha_tpa_doc}' and attached_to_doctype = 'Settlement Advice Downloader UI'  ORDER BY creation ASC LIMIT 1 ",as_dict = True)
            if file_url:
                self.delete_backend_files(f"{self.SITE_PATH}{file_url[0].file_url}")
                frappe.db.sql(f"DELETE FROM tabFile WHERE attached_to_name = '{self.captcha_tpa_doc}' and attached_to_doctype = 'Settlement Advice Downloader UI'  ORDER BY creation ASC LIMIT 1 ")
                frappe.db.commit()
            else:
                self.update_tpa_reference('Error')
                self.log_error('Settlement Advice Downloader UI',self.tpa,"No  captcha image found to delete ")


    def get_captcha_image(self,captcha_identifier):
        self.full_img_path = self.construct_file_url(self.SITE_PATH,self.SHELL_PATH, f"{self.tpa}full_img.png")
        self.crop_img_path = self.construct_file_url(self.SITE_PATH,self.SHELL_PATH,f"{self.tpa}_captcha.png")
        self.driver.save_screenshot(self.full_img_path)
        location =  captcha_identifier.location
        size =  captcha_identifier.size
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        img = Image.open(self.full_img_path)
        img = img.crop((left, top, right, bottom))
        img.save(self.crop_img_path)
        self.create_captcha_file()

    def get_status_count(self,status):
        frappe.db.commit()
        status_count_query = frappe.db.sql(f"SELECT count(name) AS total FROM `tabSettlement Advice Downloader UI Logins` WHERE status = '{status}' and parent ='{self.captcha_tpa_doc}' ",as_dict = True)[0]
        return status_count_query.total

    def update_settlement_advice_downloader_status(self):
         try:
             doc = frappe.get_doc('Settlement Advice Downloader UI', self.captcha_tpa_doc)
             total_logins = len(frappe.db.sql(f"SELECT name FROM `tabSettlement Advice Downloader UI Logins` WHERE parent = '{self.captcha_tpa_doc}'"))
             if self.get_status_count("Open") == 0 and self.get_status_count("InProgress") == 0:
                 if self.get_status_count("Error") != 0:
                     doc.status = "Error"
                 elif self.get_status_count("Completed") + self.get_status_count("Retry") == total_logins and self.get_status_count("Retry") !=0:
                     doc.status = "Partially Completed"
                 else:
                     doc.status = "Completed"
                 doc.save()
         except Exception as E:
             self.log_error('Settlement Advice Downloader UI',self.tpa," Status Update Failed ")

    def update_tpa_reference(self,status):
        try:
            status_query = frappe.db.sql(f"SELECT status FROM `tabSettlement Advice Downloader UI Logins` WHERE name = '{self.child_reference_name}' ",as_dict = True)
            if status_query[0].status == 'InProgress':
                frappe.db.sql(f"UPDATE `tabSettlement Advice Downloader UI Logins` SET status = '{status}' WHERE name = '{self.child_reference_name}' ")
                frappe.db.commit()
        except Exception as E:
            self.log_error('Settlement Advice Downloader UI',self.tpa, E)

    def _login(self):
        self.driver.get(self.url)
        return self.login()

    def login(self):
        return None

    def navigate(self):
        return None

    def download_from_web(self):
        return None

    def insert_run_log(self, data):
        doc=frappe.get_doc("TPA Login Credentials",self.credential_doc.name)
        doc.append("run_log",data)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return None

    def create_download_directory(self):
        self.file_name = f"{self.credential_doc.name.replace(' ', '').lower()}"
        file_path = self.files_path + self.file_name
        os.mkdir(file_path)
        self.download_directory = file_path

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
        file.folder = self.construct_file_url(self.HOME_PATH, self.SUB_DIR[0])
        file.is_private = 1
        file.file_url = "/" + self.construct_file_url(self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0], file_name)
        file.save(ignore_permissions=True)
        self.delete_backend_files(
            file_path=self.construct_file_url(self.SITE_PATH, self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0], file_name))
        file_url = "/" + self.construct_file_url(self.SHELL_PATH, file_name)
        frappe.db.commit()
        return file_url

    def log_error(self,doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()
        if self.download_directory:
            self.delete_folder(self.download_directory)
            self.download_directory = None
        if reference_name:
            self.insert_run_log({"last_executed_time":self.last_executed_time,"document_reference":"Error Record Log","reference_name":error_log.name,"status":"Error"})
            frappe.db.commit()

    def create_fileupload(self,file_url,file_name):
        file_upload_doc=frappe.new_doc("File upload")
        file_upload_doc.document_type="Settlement Advice"
        file_upload_doc.payer_type=self.credential_doc.tpa
        file_upload_doc.upload=file_url
        file_upload_doc.is_bot = 1
        file_upload_doc.file_format = 'EXCEL'
        file_upload_doc.save(ignore_permissions=True)
        self.insert_run_log({"last_executed_time":self.last_executed_time,"document_reference":"File upload","reference_name":file_upload_doc.name,"status":"Processed"})
        frappe.db.commit()

    def raise_exception(self,exception):
        raise Exception(exception)

    def _exit(self, e = None):
        if self.driver:
            self.driver.quit()
        if e:
            self.log_error('TPA Login Credentials', self.user_name, e)
        if self.is_captcha == True:
            if e:
                self.update_tpa_reference('Error')
            else:
                self.update_tpa_reference('Completed')
            self.delete_captcha_images()
            self.update_settlement_advice_downloader_status()
        self.exit()

    def exit(self):
        pass

    def convert_file_format(self,original_file,formated_file):
        #HTML
        if  self.incoming_file_type == 'HTML':
            data = pd.read_html(original_file)
            if len(data) ==1:
                data[0].to_excel(formated_file,index=False)
            else:
                self.raise_exception("MORE THAN ONE TABLE FOUND WHILE CONVERTING HTML TO EXCEL")
            self.delete_backend_files(original_file)

    def _download(self):
        self.download_from_web()
        downloaded_files_count = len(os.listdir(self.download_directory))
        if downloaded_files_count != 1:
            self.raise_exception(f"Your directory {self.download_directory} has either no file or have multiple files")
        self.convert_file_format(f"{self.download_directory}/{os.listdir(self.download_directory)[0]}",f"{self.download_directory}/{self.tpa}_formated_file.xlsx")

    def _move_to_extract(self):
        formatted_file_name = self.rename_downloaded_file(self.download_directory, self.file_name)
        self.move_file_to_extract(self.download_directory, formatted_file_name)

        self.delete_folder(self.download_directory)
        self.download_directory = None

        file_url = self.create_file_record(formatted_file_name)
        self.create_fileupload(file_url, self.file_name)

    def add_driver_argument(self):
        if self.is_headless == True:
            self.options.add_argument("--headless=new")
        frappe.db.commit()
        extension_path = (frappe.db.sql("SELECT path FROM `tabExtension Reference` WHERE parent = 'CarehealthDownloader' ",
                                  pluck='path'))
        if extension_path:
            for path in extension_path:
                self.options.add_argument(f'--load-extension={path}')

    def download(self, tpa_doc, chunk_doc=None, child=None, parent=None):
        try:
            chunk.update_status(chunk_doc, "InProgress")
            self.set_self_variables(tpa_doc,child,parent) if child and parent != None else self.set_self_variables(tpa_doc)
            self._init()
            self._login()
            self.navigate()
            self._download()
            self._move_to_extract()
            self._exit()
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")
            self._exit(e)

    def _init(self):
        self.create_download_directory()
        prefs = {"download.default_directory": self.download_directory + "/"}
        self.options.add_experimental_option("prefs", prefs)
        if frappe.db.exists("SA Downloader Configuration", {"name": self.executing_child_class}):
            self.add_driver_argument()
        else:
            self.raise_exception(" SA Downloader Configuration not found ")
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver,  10)

    def init(self):
        pass

