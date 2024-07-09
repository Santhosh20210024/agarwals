import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class StarVitrayaDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def login(self):
       
        user = self.wait.until(EC.visibility_of_element_located((By.ID,'email')))
        user.send_keys(self.user_name)
        password = self.wait.until(EC.visibility_of_element_located((By.ID,'password')))
        password.send_keys(self.password)
        
    def navigate(self):
        self.driver.find_element(By.ID,'loginBtn1').click()

    def download_from_web(self,temp_from_date=None,temp_to_date=None):
        from_date = self.from_date.strftime('%d-%m-%Y') if temp_from_date is None else temp_from_date.strftime('%d-%m-%Y')
        to_date = self.to_date.strftime('%d-%m-%Y') if temp_to_date is None else temp_to_date.strftime('%d-%m-%Y')
        from_to_date = self.wait.until(EC.visibility_of_element_located((By.ID,'mat-input-0')))
        from_to_date.click()
        from_to_date.clear()
        from_to_date.send_keys(f'{from_date} - {to_date}')
        button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='ok']")))
        button.click()
        dropdown = self.driver.find_element(By.CSS_SELECTOR, ".dspInBlk > select")
        time.sleep(5)
        dropdown.find_element(By.XPATH, "//option[. = 'Dashboard Report']").click()
        time.sleep(10)
        dropdown.find_element(By.XPATH, "//option[. = 'Download Reports']").click()

    def download_from_web_with_date_range(self,temp_from_date,temp_to_date,logout):
        self.download_from_web(temp_from_date,temp_to_date)
