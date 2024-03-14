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
        self.self.driver.find_element(By.ID,'btnLogin').click() #login

    def navigate(self):
        self.driver.get('https://webace.goodhealthtpa.in/Provider/ProviderDownloadMIS.aspx')

    def download_from_web(self):
        self.driver.find_element(By.ID, "ContentPlaceHolder1_ddlFromMonth").click()
        dropdown =  self.driver.find_element(By.ID, "ContentPlaceHolder1_ddlFromMonth")
        dropdown.find_element(By.XPATH, "//option[. = 'Feb']").click() #From month
        self.driver.find_element(By.ID, "ContentPlaceHolder1_ddlFromYear").click()
        dropdown = self.driver.find_element(By.ID, "ContentPlaceHolder1_ddlFromYear")
        dropdown.find_element(By.XPATH, "//option[. = '2022']").click() #From year
        self.driver.find_element(By.ID, "ContentPlaceHolder1_ddlToMonth").click()
        dropdown = self.driver.find_element(By.ID, "ContentPlaceHolder1_ddlToMonth")
        dropdown.find_element(By.XPATH, "//option[. = 'Jun']").click() #To Month
        self.driver.find_element(By.ID, "ContentPlaceHolder1_ddlToYear").click()
        dropdown =self.driver.find_element(By.ID, "ContentPlaceHolder1_ddlToYear")
        dropdown.find_element(By.XPATH, "//option[. = '2022']").click() #To Year
        self.driver.find_element(By.ID, "ddlClaimStatus").click()
        dropdown = self.driver.find_element(By.ID, "ddlClaimStatus")
        dropdown.find_element(By.XPATH, "//option[. = 'Settled']").click()
        self.driver.find_element(By.ID,'btnSubmit').click()
        time.sleep(5)