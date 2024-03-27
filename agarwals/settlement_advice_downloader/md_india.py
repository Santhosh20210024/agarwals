import frappe
from agarwals.settlement_advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class MDIndiaDownloader(SeleniumDownloader):
    def __init__(self,tpa_name,branch_code,last_executed_time):
        self.tpa=tpa_name
        self.branch_code=branch_code
        self.last_executed_time=last_executed_time
        SeleniumDownloader.__init__(self)
        
    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,'ProviderCode')))
        self.driver.find_element(By.ID,'ProviderCode').send_keys(self.user_name)
        self.driver.find_element(By.ID,'ProviderPassword').send_keys(self.password)
        self.driver.find_element(By.ID,'btnSubmit').click()

    def navigate(self):
        self.wait.until(EC.visibility_of_element_located,((By.XPATH, "//span[contains(@class, 'subnav-btn') and text()='Claim Details']")))
        claim_details =self.driver.find_element(By.XPATH, "//span[contains(@class, 'subnav-btn') and text()='Claim Details']")
        claim_details.click()
        self.driver.find_element(By.LINK_TEXT,'Paid Claim Details').click()
        time.sleep(5)

    def download_from_web(self):
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "btn-default")))
        self.driver.find_element(By.CLASS_NAME, "btn-default").click()
        time.sleep(15)