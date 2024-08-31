import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class MDIndiaDownloader(SeleniumDownloader):

    def check_login_status(self)->bool:
        try:
            self.min_wait.until(EC.visibility_of_element_located((By.XPATH,"//div[contains(@class, 'validation-summary-errors')]//li[contains(text(), 'Invalid Rohini / Provider Code or Password')]"))).text
            return False
        except:
            return True

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,'ProviderCode'))).send_keys(self.user_name)
        self.wait.until(EC.visibility_of_element_located((By.ID,'ProviderPassword'))).send_keys(self.password)
        self.wait.until(EC.element_to_be_clickable((By.ID,'btnSubmit'))).click()

    def navigate(self):
        self.wait.until(EC.visibility_of_element_located,((By.XPATH, "//span[contains(@class, 'subnav-btn') and text()='Claim Details']")))
        claim_details =self.driver.find_element(By.XPATH, "//span[contains(@class, 'subnav-btn') and text()='Claim Details']")
        claim_details.click()
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT,'Paid Claim Details'))).click()

    def download_from_web(self):
        self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-default"))).click()
        time.sleep(15)