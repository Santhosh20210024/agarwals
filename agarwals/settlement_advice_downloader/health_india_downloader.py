import frappe
from agarwals.settlement_advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class HealthIndiaDownloader(SeleniumDownloader):
    def __init__(self):
        super().__init__()
        self.portal ='Health India'
        self.url = 'https://healthindiatpa.com/Logins/LoginProvider.aspx'
        self.count = 0

    def login(self):
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID,'ctl00_ContentPlaceHolder1_txtprovidercode')))
            user_name = self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_txtprovidercode')
            user_name.send_keys(self.user_name)
            password = self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_txtproviderpassword')
            password.send_keys(self.password)
            self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_btnLogin').click()
        except Exception as e:
            print(e)

    def navigate(self):
        try:
            claim_count =self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_lblsettled').get_attribute("innerHTML")
            self.count = claim_count
            if  claim_count == 0:
                return None  
            else:
                url = 'https://healthindiatpa.com/Provider/claimshome.aspx?type=claims_settled'
                self.driver.get(url)
        except Exception as e:
            print(e)


    def download(self):
        try:
            if self.count ==0:
                return False
            else:
                self.wait.until(EC.visibility_of_element_located,((By.ID,'ctl00_ContentPlaceHolder1_lnk_ExportToExcel')))
                self.driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_lnk_ExportToExcel').click()
                time.sleep(10)
                return True
        except Exception as e:
            print (e)

@frappe.whitelist()
def initiator():
    HealthIndiaDownloader().process()