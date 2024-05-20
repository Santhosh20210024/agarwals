import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class GoodHealthDownloader(SeleniumDownloader):
    def __init__(self):
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

    def setFieldValue(self, field_id, field_value):
        element = self.wait.until(EC.visibility_of_element_located((By.ID, field_id)))
        self.driver.execute_script("arguments[0].setAttribute('type', 'text')", element)
        element.send_keys(field_value)

    def download_from_web(self):
        _from = self.from_date.strftime("%b %Y").split(" ")
        _to = self.to_date.strftime("%b %Y").split(" ")
        self.setFieldValue('ContentPlaceHolder1_ddlFromMonth', _from[0])
        self.setFieldValue('ContentPlaceHolder1_ddlFromYear', _from[1])

        self.setFieldValue('ContentPlaceHolder1_ddlToMonth', _to[0])
        self.setFieldValue('ContentPlaceHolder1_ddlToYear', _to[1])

        time.sleep(5)
        dropdown = self.driver.find_element(By.ID, "ddlClaimStatus")
        dropdown.find_element(By.XPATH, "//option[. = 'Settled']").click()
        self.driver.find_element(By.ID,'btnSubmit').click()
        time.sleep(10)
