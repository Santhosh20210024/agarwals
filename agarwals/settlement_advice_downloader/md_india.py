import frappe
from agarwals.settlement_advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class MDIndiaDownloader(SeleniumDownloader):
    def __init__(self):
        super().__init__()
        self.portal ='Health India'
        self.url = 'https://eclaim.mdindia.com:94/'
        
    def login(self):
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID,'ProviderCode')))
            self.driver.find_element(By.ID,'ProviderCode').send_keys(self.user_name)
            self.driver.find_element(By.ID,'ProviderPassword').send_keys(self.password)
            self.driver.find_element(By.ID,'btnSubmit').click()
        except Exception as e:
            print(e)

    def navigate(self):
        try:
            self.wait.until(EC.visibility_of_element_located,((By.XPATH, "//span[contains(@class, 'subnav-btn') and text()='Claim Details']")))
            claim_details =self.driver.find_element(By.XPATH, "//span[contains(@class, 'subnav-btn') and text()='Claim Details']")
            claim_details.click()
            self.driver.find_element(By.LINK_TEXT,'Paid Claim Details').click()
            time.sleep(5)
        except Exception as e:
            print(e)


    def download(self):
        try:
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "btn-default")))
            self.driver.find_element(By.CLASS_NAME, "btn-default").click()
        except Exception as e:
            print (e)

@frappe.whitelist()
def initiator():
    MDIndiaDownloader().process()