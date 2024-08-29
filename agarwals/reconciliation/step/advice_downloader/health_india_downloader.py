import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class HealthIndiaDownloader(SeleniumDownloader):

    def check_login_status(self)->bool:
        try:
            self.min_wait.until(EC.visibility_of_element_located((By.XPATH,"//span[@id='ctl00_ContentPlaceHolder1_lblMessage' and text()='Invalid User name / password.']")))
            return False
        except:
            return True

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,'ctl00_ContentPlaceHolder1_txtprovidercode'))).send_keys(self.user_name)
        self.wait.until(EC.visibility_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_txtproviderpassword'))).send_keys(self.password)
        self.wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_btnLogin'))).click()


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