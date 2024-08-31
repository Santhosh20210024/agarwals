import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class SafewayDownloader(SeleniumDownloader):

    def check_login_status(self):
        try:
            error = self.min_wait.until(EC.visibility_of_element_located((By.ID,'ctl00_ContentPlaceHolder1_lblerr'))).text
            if error == 'Invalid UserName or Password ..':
                return False
        except:
            return True

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txt_username"))).send_keys(self.user_name) #username
        self.wait.until(EC.visibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txt_pwd"))).send_keys(self.password) #password
        self.wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_ImageButton1"))).click() #login button

    def navigate(self):
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Claim MIS"))).click()
        self.wait.until(EC.visibility_of_element_located((By.ID,"ctl00_ContentPlaceHolder1_DtpFrom_Date5"))).send_keys(self.from_date.strftime("%d/%m/%Y")) # From Date
        self.wait.until(EC.visibility_of_element_located((By.ID,"ctl00_ContentPlaceHolder1_Dtpto_Date5"))).send_keys(self.to_date.strftime("%d/%m/%Y")) #To Date
        self.wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_Button1"))).click() #Submit

    def download_from_web(self):
        self.wait.until(EC.visibility_of_element_located,((By.ID, "ctl00_ContentPlaceHolder1_lbltot")))
        record_count = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_lbltot")
        inner_html = record_count.get_attribute("innerHTML")
        if inner_html == 'No Record Found':
            return False
        else:
            self.wait.until(EC.visibility_of_element_located,(By.ID,"ctl00_ContentPlaceHolder1_btnExportInXLS"))
            self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btnExportInXLS").click() 
            time.sleep(10)
            return True