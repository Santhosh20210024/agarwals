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
from twocaptcha import TwoCaptcha
from agarwals.reconciliation import chunk
from PIL import Image
import os
import shutil
import pandas as pd
import openpyxl
import glob
from io import StringIO

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
        self.formatted_file_name = None
        self.sandbox_mode = True
        self.previous_files_count = None
        self.is_date_limit  = 0
        self.date_limit_period = 0
        self.enable_captcha_api = None
        self.folder_path = None


    def construct_file_url(*args):
        list_of_items = []
        for arg in args:
            if type(arg)==str:
                list_of_items.append(arg)
        formatted_url = '/'.join(list_of_items)
        return formatted_url

    def update_retry(self):
        doc = frappe.get_doc('TPA Login Credentials',self.credential_doc.name)
        doc.retry = 1
        doc.save()

    def set_self_variables(self, tpa_doc ,child = None, parent = None):
        self.credential_doc = tpa_doc
        if self.credential_doc:
            self.user_name = self.credential_doc.user_name
            self.password = self.credential_doc.password
            self.executing_child_class = self.credential_doc.executing_method
            if frappe.db.exists("SA Downloader Configuration",{"name":self.executing_child_class}):
                configuration_values = frappe.db.sql(f"SELECT * FROM `tabSA Downloader Configuration` WHERE `name`='{self.executing_child_class}'",as_dict=True)[0]
                self.is_captcha = True if configuration_values.is_captcha == 1 else False
                self.is_headless = True if configuration_values.is_headless == 1 else False
                self.incoming_file_type = configuration_values.incoming_file_type
                self.max_wait_time = configuration_values.captcha_entry_duration
                self.url = configuration_values.website_url
                self.from_date = configuration_values.from_date
                self.sandbox_mode = True if configuration_values.sandbox_mode == 1 else False
                self.to_date = configuration_values.to_date if configuration_values.to_date else frappe.utils.now_datetime().date()
                self.is_date_limit = configuration_values.is_date_limit
                self.date_limit_period = configuration_values.date_limit_period
            control_panel = frappe.get_doc('Control Panel')
            if control_panel:
                self.enable_captcha_api = control_panel.enable_captcha_api
            else:
                self.raise_exception(" SA Downloader Configuration not found ")
            if child and parent is not None:
                self.child_reference_name = child
                self.captcha_tpa_doc = parent
                self.tpa = self.credential_doc.name
        else:
            self.log_error('TPA Login Credentials',None,"No Credential for the given input")

    def get_captcha_value(self,captcha_type=None,sitekey=None):
        try:


            if self.enable_captcha_api == 0:
                captcha = ''
                end_time = time.time() + self.max_wait_time
                while time.time() < end_time:
                    frappe.db.commit()
                    captcha_value = frappe.db.sql(f"SELECT captcha FROM `tabSettlement Advice Downloader UI` WHERE name = '{self.captcha_tpa_doc}'",as_dict = True)
                    if captcha_value[0].captcha:
                        captcha = captcha_value[0].captcha
                        break
                    time.sleep(5)
                return captcha if captcha !='' else None

            elif self.enable_captcha_api == 1:

                #api method
                control_panel = frappe.get_doc('Control Panel')
                api_key =control_panel.captcha_api_key
                api_key = os.getenv('APIKEY_2CAPTCHA', api_key)
                solver = TwoCaptcha(api_key)
                if captcha_type == "Normal Captcha":
                    result = solver.normal(file=self.crop_img_path,
                                           minLen=1,
                                           maxLen=20,
                                           phrase=1,
                                           caseSensitive=1,
                                           lang='en')
                    return result,api_key
                elif captcha_type == "ReCaptcha":
                    result = solver.recaptcha(
                        sitekey=sitekey,
                        url=self.url)
                    return result,api_key
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def extract_table_data(self, table_id):
        table = self.wait.until(EC.presence_of_element_located((By.ID, table_id)))
        table_html = table.get_attribute('outerHTML')
        with open(f'{self.download_directory}/{self.tpa}.html', 'w') as file:
            file.write(table_html)

    def attach_captcha_img(self,file_url=None):
        captcha_reference_doc = frappe.get_doc('Settlement Advice Downloader UI',self.captcha_tpa_doc)
        captcha_reference_doc.captcha_img = file_url
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
            if self.enable_captcha_api == 0:
                file_url = frappe.db.sql(f"SELECT file_url FROM tabFile WHERE attached_to_name = '{self.captcha_tpa_doc}' and attached_to_doctype = 'Settlement Advice Downloader UI'  ORDER BY creation ASC LIMIT 1 ",as_dict = True)
                if file_url:
                    self.delete_backend_files(f"{self.SITE_PATH}{file_url[0].file_url}")
                    frappe.db.sql(f"DELETE FROM tabFile WHERE attached_to_name = '{self.captcha_tpa_doc}' and attached_to_doctype = 'Settlement Advice Downloader UI'  ORDER BY creation ASC LIMIT 1 ")
                    frappe.db.commit()
                else:
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

        if self.enable_captcha_api == 0:
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
                parent_doc = frappe.get_doc('Settlement Advice Downloader UI', self.captcha_tpa_doc)
                parent_doc.captcha_img = ''
                doc = frappe.get_doc("Settlement Advice Downloader UI Logins", self.child_reference_name)
                doc.update({
                    "status":status
                })
                parent_doc.logins.append(doc)
                parent_doc.save(ignore_permissions = True)
                frappe.db.commit()
        except Exception as E:
            self.log_error('Settlement Advice Downloader UI',self.tpa, E)

    def _login(self):
        self.driver.get(self.url)
        self.driver.maximize_window()
        return self.login()

    def login(self):
        return None

    def navigate(self):
        return None

    def download_from_web(self):
        return None

    def download_from_web_with_date_range(self,temp_from_date, temp_to_date):
        pass

    def insert_run_log(self, data):
        doc=frappe.get_doc("TPA Login Credentials",self.credential_doc.name)
        doc.append("run_log",data)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return None

    def create_download_directory(self):
        self.file_name = f"{self.credential_doc.name.replace(' ', '').lower()}"
        self.folder_path = self.files_path + "Settlement Advice/" + f"{self.credential_doc.tpa}/"
        file_path =self.folder_path + self.file_name
        os.mkdir(file_path)
        self.download_directory = file_path
        self.previous_files_count = len(os.listdir(self.download_directory))


    def rename_downloaded_file(self, download_directory, file_name,temp_from_date=None,temp_to_date=None):
        from_date = self.from_date if temp_from_date is None else temp_from_date
        to_date = self.to_date if temp_to_date is None else temp_to_date
        get_all_files =  glob.glob(os.path.join(download_directory,'*'))
        recent_downloaded_file = max(get_all_files,key=os.path.getctime)

        if self.incoming_file_type == 'HTML':
            self.convert_file_format(f"{self.download_directory}/{recent_downloaded_file.split('/')[-1]}",
                                     f"{self.download_directory}/{self.tpa}_formated_file.xlsx")

        original_file_name = recent_downloaded_file.split('/')[-1] if self.incoming_file_type == 'Excel' else f"{self.tpa}_formated_file.xlsx"
        extension = original_file_name.split(".")[-1]
        formatted_file_name = file_name + f"{from_date}_{to_date}" + "." + extension if self.from_date is not None else file_name + "." + extension
        os.rename(download_directory + '/' + original_file_name, download_directory + '/' + formatted_file_name)
        return formatted_file_name

    def move_file(self, download_directory,formatted_file_name):
        shutil.move(download_directory + "/" + formatted_file_name, self.folder_path + formatted_file_name)

    def delete_folder(self,download_directory):
        shutil.rmtree(download_directory)

    def delete_backend_files(self,file_path=None):
        if os.path.exists(file_path):
            os.remove(file_path)

    def create_file_record(self, file_name):
        file = frappe.new_doc("File")
        file.folder = self.construct_file_url(self.HOME_PATH,self.SUB_DIR[0])
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
        if self.download_directory:
            self.delete_folder(self.download_directory)
            self.download_directory = None

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
        try:
            with open(original_file, 'r', encoding='utf-8') as file:
                html_content = file.read()
                html_io = StringIO(html_content)
                data = pd.read_html(html_io)
        except Exception as e:
            # self.delete_backend_files(original_file)
            self.raise_exception(f"An error occurred while reading the file: {e}")
        if len(data) == 1:
            data[0].to_excel(formated_file, index=False)
            self.delete_backend_files(original_file)
        else:
            # self.delete_backend_files(original_file)
            self.raise_exception("MORE THAN ONE TABLE FOUND WHILE CONVERTING HTML TO EXCEL")


    def download_with_date_range(self):
        run = True
        temp_from_date = self.from_date
        period =  self.date_limit_period - 1
        while run:
            self.previous_files_count = len(os.listdir(self.download_directory))
            temp_to_date = temp_from_date + timedelta(days=period)
            if temp_to_date >= self.to_date:
                if temp_to_date > self.to_date:
                    temp_to_date = self.to_date
                self.download_from_web_with_date_range(temp_from_date,temp_to_date)
                self.format_downloaded_file(temp_from_date,temp_to_date)
                run = False
            else:
                self.download_from_web_with_date_range(temp_from_date, temp_to_date)
                self.format_downloaded_file(temp_from_date, temp_to_date)
                temp_from_date = temp_to_date + timedelta(days=1)



    def _download(self):
        if self.is_date_limit == 1 and self.date_limit_period != 0:
            self.download_with_date_range()
        else:
            self.download_from_web()
            self.format_downloaded_file()
    def format_downloaded_file(self,temp_from_date=None,temp_to_date=None):
        downloaded_files_count = len(os.listdir(self.download_directory))
        if self.previous_files_count == downloaded_files_count:
            self.log_error(doctype_name='TPA Login Credentials', reference_name= self.user_name , error_message="File Not Found or No Record Found")
        else:
            self.formatted_file_name = self.rename_downloaded_file(self.download_directory, self.file_name,temp_from_date,temp_to_date)
            self.move_file(self.download_directory,self.formatted_file_name)
    def _move_to_extract(self):
        self.move_file_to_extract(self.download_directory,formatted_file_name=self.formatted_file_name)
        self.delete_folder(self.download_directory)
        self.download_directory = None
        file_url = self.create_file_record(self.formatted_file_name)
        self.create_fileupload(file_url, self.file_name)

    def add_driver_argument(self):
        if self.is_date_limit == 1:
            self.options.add_experimental_option('detach', True)
        if self.sandbox_mode == False:
            self.options.add_argument('--no-sandbox')
            self.options.add_argument('--disable-dev-shm-usage')
        if self.is_headless == True:
            self.options.add_argument("--headless=new")
        frappe.db.commit()
        extension_path = (frappe.db.sql(f"SELECT path FROM `tabExtension Reference` WHERE parent = '{self.executing_child_class}' ",
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
        self.wait = WebDriverWait(self.driver,  30)

    def init(self):
        pass


