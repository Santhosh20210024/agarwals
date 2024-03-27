import frappe
from agarwals.settlement_advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class GoodHealthDownloader(SeleniumDownloader):
    def __init__(self,tpa_name,branch_code,last_executed_time):
        self.tpa=tpa_name
        self.branch_code=branch_code
        self.last_executed_time=last_executed_time
        SeleniumDownloader.__init__(self)

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,'txtUsrName')))
        username = self.driver.find_element(By.ID,'txtUsrName')
        username.send_keys(self.user_name) # User name
        password = self.driver.find_element(By.ID,'txtPassword')
        password.send_keys(self.password) # Password 
        self.driver.find_element(By.ID,'btnLogin').click() #login

    def navigate(self):
        self.driver.get('https://webace.goodhealthtpa.in/Provider/ProviderDownloadMIS.aspx')
        time.sleep(5)

    def download_from_web(self):
        from_month_year = self.from_date.strftime("%b %Y").split(" ")
        to_month_year = self.to_date.strftime("%b %Y").split(" ")
        from_month = self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_ddlFromMonth')))
        from_year = self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_ddlFromYear')))
        self.driver.execute_script("arguments[0].setAttribute('type', 'text')", from_month)
        self.driver.execute_script("arguments[0].setAttribute('type', 'text')", from_year)
        to_month = self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_ddlToMonth')))
        to_year = self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_ddlToYear')))
        self.driver.execute_script("arguments[0].setAttribute('type', 'text')", to_month)
        self.driver.execute_script("arguments[0].setAttribute('type', 'text')", to_year)
        from_month.send_keys(f'{from_month_year[0]}')
        from_year.send_keys(f'{from_month_year[1]}')
        to_month.send_keys(f'{to_month_year[0]}')
        to_year.send_keys(f'{to_month_year[1]}')
        time.sleep(5)
        dropdown = self.driver.find_element(By.ID, "ddlClaimStatus")
        dropdown.find_element(By.XPATH, "//option[. = 'Settled']").click()
        self.driver.find_element(By.ID,'btnSubmit').click()
        time.sleep(10)
