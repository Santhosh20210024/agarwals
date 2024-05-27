import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class HealthIndiaDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)
        
    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,'ctl00_ContentPlaceHolder1_txtprovidercode')))
        user_name = self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_txtprovidercode')
        user_name.send_keys(self.user_name)
        password = self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_txtproviderpassword')
        password.send_keys(self.password)
        self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_btnLogin').click()

    def navigate(self):
        time.sleep(5)
        claim_count =self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_lblsettled').get_attribute("innerHTML")
        if  claim_count == 0:
            self.raise_exception("Claim count should not be 0")
        else:
            panel_footers = self.driver.find_elements(By.CSS_SELECTOR, '.panel-footer')
            panel_footers[-1].click()
            time.sleep(5)

    def download_from_web(self):
        self.wait.until(EC.visibility_of_element_located,((By.ID,'ctl00_ContentPlaceHolder1_lnk_ExportToExcel')))
        self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_lnk_ExportToExcel').click()
        time.sleep(10)