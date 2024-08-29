import frappe
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime,timedelta
from agarwals.utils.error_handler import log_error as error_handler
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
import random
from agarwals.utils.file_util import PROJECT_FOLDER,HOME_PATH,SHELL_PATH,SUB_DIR,SITE_PATH

class SeleniumDownloader:
    def __init__(self):
        self.extract_first_table = False
        self.format_file_in_parent = True
        self.SHELL_PATH = SHELL_PATH
        self.SITE_PATH = SITE_PATH
        self.last_executed_time = frappe.utils.now_datetime()
        self.public_path = "public/files"
        self.full_img_path = None
        self.crop_img_path = None
        self.webdriver_wait_time = 60
        self.file_not_found_remarks = ""
        self.captcha_alert = "Invalid Captcha"

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

    def get_captcha_value(self,captcha_type=None,sitekey=None):
        if self.enable_captcha_api == 0:
            captcha = None
            end_time = time.time() + self.max_wait_time
            while time.time() < end_time:
                frappe.db.commit()
                captcha_value = frappe.db.sql(f"SELECT captcha FROM `tabSettlement Advice Downloader UI` WHERE name = '{self.captcha_tpa_doc}'",as_dict = True)
                if captcha_value[0].captcha:
                    captcha = captcha_value[0].captcha
                    break
                time.sleep(5)
            return captcha
        elif self.enable_captcha_api == 1:
            #api method
            api_key = os.getenv('APIKEY_2CAPTCHA',self.api_key)
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

    def extract_table_data(self, table_element):
        table_html = table_element.get_attribute('outerHTML')
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
                    self.log_error(doctype_name = 'Settlement Advice Downloader UI',reference_name=self.tpa,error_message = "No  captcha image found to delete ")


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
         except Exception as e:
             self.log_error('Settlement Advice Downloader UI',f" Status Update Failed due to {e}",self.tpa)

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
            self.log_error('Settlement Advice Downloader UI',E,self.tpa)

    def _login(self):
        self.driver.get(self.url)
        self.driver.maximize_window()
        self.login()
        self.__check_login_status()

    def login(self):
        return None

    def __check_login_status(self):
        login_status = self.check_login_status()
        if login_status == False:
            raise ValueError("Invalid user name or password")
        elif login_status == self.captcha_alert:
            raise ValueError("Invalid Captcha")
        else:
            return

    def check_login_status(self)->bool | str | None:
        return None
    def navigate(self):
        return None

    def download_from_web(self):
        return None

    def download_from_web_with_date_range(self,temp_from_date, temp_to_date,logout):
        pass

    def insert_run_log(self, data):
        doc = frappe.get_doc(data).insert(ignore_permissions=True)
        return doc

    def create_download_directory(self):
        suffix =  f"{self.credential_doc.tpa}-{self.credential_doc.branch_code if self.credential_doc.branch_code else ''}-".replace(' ','').lower()
        self.file_name = f"{self.credential_doc.user_name}-{suffix}"
        self.folder_path = os.path.join(SITE_PATH,SHELL_PATH,PROJECT_FOLDER,'Settlement Advice',self.credential_doc.tpa) + "/"
        if not os.path.exists(self.folder_path):
            self.raise_exception("Download Directory Not Found To Download Settlement Advice")
        file_path =self.folder_path + self.file_name
        os.mkdir(file_path)
        self.download_directory = file_path
        self.previous_files_count = len(os.listdir(self.download_directory))

    def generate_random_number(self):
        numbers = []
        run = True
        while run == True:
            random_number = random.randint(1000, 99999)
            if not random_number in numbers:
                numbers.append(random_number)
                run = False
        return random_number

    def rename_downloaded_file(self, download_directory, file_name,from_date,to_date)->str:
        get_all_files =  glob.glob(os.path.join(download_directory,'*'))
        recent_downloaded_file = max(get_all_files,key=os.path.getctime)
        if self.incoming_file_type == 'HTML':
            self.convert_file_format(f"{self.download_directory}/{recent_downloaded_file.split('/')[-1]}",
                                     f"{self.download_directory}/{self.tpa}_formated_file.xlsx")
        original_file_name = recent_downloaded_file.split('/')[-1] if self.incoming_file_type != 'HTML' else f"{self.tpa}_formated_file.xlsx"
        extension = original_file_name.split(".")[-1]
        if self.from_date is not None and self.format_file_in_parent == True:
            formatted_file_name = file_name + f"{from_date}_{to_date}" + "." + extension
        elif self.from_date is not None and self.format_file_in_parent == False:
            random_number = self.generate_random_number()
            formatted_file_name = file_name + f"{from_date}_{to_date}_{random_number}" + "." + extension
        else:
            formatted_file_name = file_name + "." + extension
        os.rename(download_directory + '/' + original_file_name, download_directory + '/' + formatted_file_name)
        return formatted_file_name

    def move_file(self, download_directory,formatted_file_name):
        shutil.move(download_directory + "/" + formatted_file_name, self.folder_path + formatted_file_name)

    def delete_folder(self,download_directory):
        shutil.rmtree(download_directory)

    def delete_backend_files(self,file_path=None):
        if os.path.exists(file_path):
            os.remove(file_path)

    def log_error(self,doctype_name,error_message,reference_name = None):
        log = error_handler(error=error_message, doc=doctype_name,doc_name=reference_name)
        return log

    def raise_exception(self,exception):
        raise Exception(exception)

    def _exit(self)->None:
        try:
            # Delete Download Directory
            if self.download_directory:
                self.delete_folder(self.download_directory)
                self.download_directory = None
            # WebDriver Exits
            if self.driver:
                self.driver.quit()
            # Delete Captacha Image
            if self.is_captcha == True:
                self.delete_captcha_images()
                self.update_settlement_advice_downloader_status()
        except Exception as e:
            self.update_status_and_log(status='Error',remarks=e)


    def convert_file_format(self,original_file,formated_file):
        #HTML
        try:
            with open(original_file, 'r', encoding='utf-8') as file:
                html_content = file.read()
                html_io = StringIO(html_content)
                data = pd.read_html(html_io)
        except Exception as e:
            self.raise_exception(f"An error occurred while reading the file: {e}")
        if len(data) == 1 or self.extract_first_table == True:
            data[0].to_excel(formated_file, index=False)
            self.delete_backend_files(original_file)
        else:
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
                self.download_from_web_with_date_range(temp_from_date,temp_to_date,logout=1)
                self.format_downloaded_file(temp_from_date,temp_to_date)
                run = False
            else:
                self.download_from_web_with_date_range(temp_from_date, temp_to_date,logout=0)
                self.format_downloaded_file(temp_from_date, temp_to_date)
                temp_from_date = temp_to_date + timedelta(days=1)

    def _download(self):
        if self.is_date_limit == 1 and self.date_limit_period != 0:
            self.download_with_date_range()
        else:
            self.download_from_web()
            if self.format_file_in_parent == True:
                self.format_downloaded_file()

    def format_downloaded_file(self,temp_from_date=None,temp_to_date=None):
        downloaded_files_count = len(os.listdir(self.download_directory))
        from_date = self.from_date if temp_from_date is None else temp_from_date
        to_date = self.to_date if temp_to_date is None else temp_to_date
        if self.previous_files_count == downloaded_files_count:
            self.file_not_found_remarks += f"\nFile Not Found for the Date Range Between {self.from_date} and {self.to_date}"
        else:
            self.formatted_file_name = self.rename_downloaded_file(self.download_directory, self.file_name,from_date,to_date)
            self.move_file(self.download_directory,self.formatted_file_name)

    def add_driver_argument(self):
        self.options.add_argument('--log-level=3')
        if self.allow_insecure_file == True:
            self.options.add_argument('--disable-features=InsecureDownloadWarnings')
        if self.is_date_limit == 1:
            self.options.add_experimental_option('detach', True)
        if self.sandbox_mode == False:
            self.options.add_argument('--no-sandbox')
            self.options.add_argument('--disable-dev-shm-usage')
        if self.is_headless == True:
            self.options.add_argument("--headless=new")
        extension_path = (frappe.db.sql(f"SELECT path FROM `tabExtension Reference` WHERE parent = '{self.executing_child_class}' ",
                                  pluck='path'))
        if extension_path:
            for path in extension_path:
                self.options.add_argument(f'--load-extension={path}')

    def update_status_and_log(self, status: str, retry: int = 0, remarks: str = None) -> None:
        """
        Update the status of the TPA Login Credentials document  and log the result .
        Args:
            status (str): The status to set on the document.
            retry (int, optional): The retry count. Defaults to 0.
            remarks (str, optional): Remarks for logging. Defaults to None.
        """
        try:
            # Update TPA Login Credentials Status
            doc = frappe.get_doc("TPA Login Credentials" , self.credential_doc.name)
            doc.status,doc.retry  = status,retry
            # Update Settlement Advice ui downloader if SA ui downloader enabled
            if self.is_captcha:
                if retry == 1:
                    self.update_tpa_reference('Retry')
                elif status == 'Valid':
                    self.update_tpa_reference('Completed')
                else:
                    self.update_tpa_reference('Error')
            # logging
            log_data = {"doctype": "SA Downloader Run Log",
                        "last_executed_time": self.last_executed_time,
                        "document_reference": "TPA Login Credentials",
                        "parent1": self.credential_doc.name,
                        "tpa_name": self.credential_doc.tpa,
                        "remarks": f"{self.file_not_found_remarks} \n {str(remarks) if remarks else ''}" or None
                        }
            if status == 'Error' and retry == 0:
                error_log = self.log_error(doctype_name='TPA Login Credentials',error_message=remarks,reference_name=self.tpa)
                log_data.update({"document_reference": "Error Record Log", "reference_name": error_log.name,"status": "Error"})
            elif self.file_not_found_remarks or status == 'Info':
                log_data.update({"status":"Info"})
            else:
                log_data.update({"status": "Warning","remarks": remarks}) if status == 'Invalid' or retry == 1 else log_data.update({"status": "Processed"})
            log_doc = self.insert_run_log(log_data)
            doc.last_run_log_id = log_doc.name
            doc.save()
        except Exception as e:
            self.log_error(doctype_name='TPA Login Credentials',error_message=e,reference_name=self.tpa if self.tpa else None)

    def web_driver_init(self):
        self.options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": self.download_directory + "/"}
        self.options.add_experimental_option("prefs", prefs)
        self.add_driver_argument()
        self.driver = webdriver.Chrome(options=self.options)
        self.actions = ActionChains(self.driver)
        self.wait = WebDriverWait(self.driver, self.webdriver_wait_time)
        self.min_wait = WebDriverWait(self.driver,10)

    def load_credential_doc(self,tpa_doc,child,parent):
        self.credential_doc = tpa_doc
        if self.credential_doc:
            self.user_name = self.credential_doc.user_name
            self.password = self.credential_doc.password
            self.executing_child_class = self.credential_doc.executing_method
            self.tpa = self.credential_doc.name
            if child and parent is not None:
                self.child_reference_name = child
                self.captcha_tpa_doc = parent
        else:
            self.raise_exception('TPA Credential Doc Not Found')

    def load_configuration(self)->None:
        configuration_values = frappe.db.sql(
            f"SELECT * FROM `tabSA Downloader Configuration` WHERE `name`='{self.executing_child_class}'",
            as_dict=True
        )
        if configuration_values:
            configuration_values = configuration_values[0]
            self.is_captcha = configuration_values.is_captcha
            self.is_headless = configuration_values.is_headless
            self.incoming_file_type = configuration_values.incoming_file_type
            self.max_wait_time = configuration_values.captcha_entry_duration
            self.url = configuration_values.website_url or self.raise_exception("Website URL Not Found,Please Check SA Downloader Configuration")
            self.to_date = configuration_values.to_date or frappe.utils.now_datetime().date()
            self.from_date = configuration_values.from_date or self.to_date - timedelta(days=29)
            self.sandbox_mode = configuration_values.sandbox_mode
            self.is_date_limit = configuration_values.is_date_limit
            self.date_limit_period = configuration_values.date_limit_period
            self.allow_insecure_file = configuration_values.allow_insecure_file
            control_panel = frappe.get_doc('Control Panel')
            if control_panel:
                self.enable_captcha_api = control_panel.enable_captcha_api
                self.api_key = control_panel.captcha_api_key
            else:
                self.raise_exception(" SA Downloader Configuration not found ")
        else:
            self.raise_exception(" SA Downloader Configuration not found ")

    def download(self, tpa_doc, chunk_doc=None, child=None, parent=None):
        try:
            chunk.update_status(chunk_doc, "InProgress")
            self.load_credential_doc(tpa_doc,child,parent)
            self.load_configuration()
            self.create_download_directory()
            self.web_driver_init()
            self._login()
            self.navigate()
            self._download()
            self.update_status_and_log('Valid')
            chunk.update_status(chunk_doc, "Processed")
        except ValueError as e:
            if str(e) in 'Invalid user name or password':
                self.update_status_and_log(status='Invalid', remarks=e)
            elif str(e) in 'Invalid Captcha':
                self.update_status_and_log(status='Error',retry=1,remarks=e)
            else:
                self.update_status_and_log(status='Error')
            chunk.update_status(chunk_doc, "Error")
        except Exception as e:
            self.update_status_and_log('Error',remarks=e)
            chunk.update_status(chunk_doc, "Error")
        finally:
            self._exit()








