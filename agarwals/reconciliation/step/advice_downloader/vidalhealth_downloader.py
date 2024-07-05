import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class VidalHealthDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)
        
    def login(self):
        username =  self.wait.until(EC.visibility_of_element_located((By.ID,'hosUserID')))
        username.send_keys(self.user_name)
        user_password = self.driver.find_element(By.ID,'hosPassword')
        user_password.send_keys(self.password)
        self.driver.find_element(By.CLASS_NAME,'vd-btn-primary').click()

    def navigate(self):
        time.sleep(5)
        self.driver.execute_script("onSetSubLinks('reports','reports');")

    def download_from_web(self,temp_from_date=None,temp_to_date=None):
        formated_from_date = self.from_date.strftime("%d/%m/%Y") if temp_from_date is None else temp_from_date.strftime("%d/%m/%Y")
        formated_to_date = self.to_date.strftime("%d/%m/%Y") if temp_to_date is None else temp_to_date.strftime("%d/%m/%Y")
        from_date = self.wait.until(EC.visibility_of_element_located((By.ID,'datetimepicker4')))
        to_date = self.wait.until(EC.visibility_of_element_located((By.ID,'datetimepicker5')))
        from_date.click()
        self.driver.execute_script("arguments[0].value = '';", from_date)
        from_date.send_keys(formated_from_date)
        to_date.click()
        self.driver.execute_script("arguments[0].value = '';", to_date)
        to_date.send_keys(formated_to_date)
        self.driver.find_element(By.CLASS_NAME,'vd-btn-primary').click()
        time.sleep(10)

    def download_from_web_with_date_range(self,temp_from_date,temp_to_date,logout):
        self.download_from_web(temp_from_date,temp_to_date)

        
