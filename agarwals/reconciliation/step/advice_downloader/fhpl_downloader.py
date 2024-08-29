import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
import time


class FHPLDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def check_login_status(self)->bool:
        try:
            status_message = self.min_wait.until(EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_lblError'))).text
            if status_message == 'Invalid UserName / Password':
                return False
        except:
            return True

    def login(self):
        self.wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_txtUserName'))).send_keys(
            self.user_name)
        self.wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_txtPassword'))).send_keys(
            self.password)
        self.wait.until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_btnLogin'))).click()
        login_status =  self.check_login_status()


    def navigate(self):
        return

    def download_from_web(self,temp_from_date=None,temp_to_date=None):
        from_date = self.from_date if temp_from_date is None else temp_from_date
        to_date = self.to_date if temp_to_date is None else temp_to_date
        from_date_element = self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_txtDateFrom')))
        from_date_element.click()
        from_date_element.clear()
        from_date_element.send_keys(from_date.strftime("%m/%d/%Y"))
        to_date_element = self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_txtDateTo')))
        to_date_element.click()
        to_date_element.clear()
        to_date_element.send_keys(to_date.strftime("%m/%d/%Y"))
        self.wait.until(EC.visibility_of_element_located((By.NAME, 'ctl00$ContentPlaceHolder1$btnSearch'))).click()
        time.sleep(5)
        self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_btnPortToExcel'))).click()
        time.sleep(10)

    def download_from_web_with_date_range(self,temp_from_date,temp_to_date,logout):
        self.download_from_web(temp_from_date,temp_to_date)