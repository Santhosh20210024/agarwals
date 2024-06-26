import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
import time

class EricsonDownloader(SeleniumDownloader):
    def __init__(self):
        super().__init__()  
        
    def retry_click(self, element):
        attempts = 2
        while attempts > 0:
            try:
                element.click()
                return
            except StaleElementReferenceException:
                attempts -= 1
                print("Stale element reference. Retrying...")
                time.sleep(1)
        raise Exception("Failed to click element after retries")


    def login(self):
        script = 'document.querySelector(\'a[data-target=".Hospital_Login"]\').click();'
        self.driver.execute_script(script)
        print("Hospital Login clicked")

        user_name = self.wait.until(EC.visibility_of_element_located((By.ID, "ctl00_txtHospUserName")))
        password = self.wait.until(EC.visibility_of_element_located((By.ID, "ctl00_txtHospPassword")))
        user_name.send_keys(self.user_name)
        password.send_keys(self.password)

        close_button = self.wait.until(EC.element_to_be_clickable((By.ID, "close1")))
        self.retry_click(close_button)

        login_button = self.wait.until(EC.element_to_be_clickable((By.ID, "ctl00_Button2")))
        self.retry_click(login_button)

    def navigate(self):
        claim_status_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="HospitalClaimStatus.aspx?ClaimStatus"]')))
        self.retry_click(claim_status_link)

    def download_from_web(self):
        formated_from_date = self.from_date.strftime("%d/%m/%Y")
        formated_to_date = self.to_date.strftime("%d/%m/%Y")
        from_date_input = self.wait.until(EC.visibility_of_element_located((By.ID, "ctl00_Content1_txtSettledFrom")))
        from_date_input.send_keys(formated_from_date)
        to_date_input = self.wait.until(EC.element_to_be_clickable((By.ID, "ctl00_Content1_txtSettledTo")))
        to_date_input.click()  
        
        to_date_input = self.wait.until(EC.visibility_of_element_located((By.ID, "ctl00_Content1_txtSettledTo")))
        to_date_input.send_keys(formated_to_date)
        
       
        
        search_button = self.wait.until(EC.element_to_be_clickable((By.ID, "ctl00_Content1_btnSearch")))
        self.retry_click(search_button)

       
        export_button = self.wait.until(EC.element_to_be_clickable((By.ID, "ctl00_Content1_btnSettledExport")))
        self.retry_click(export_button)
        
       
        
