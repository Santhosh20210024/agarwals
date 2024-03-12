import frappe
from agarwals.settlement_advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class GoodHealthDownloader(SeleniumDownloader):
    def __init__(self):
        super().__init__()
        self.portal ='Good Health'
        self.url = 'https://webace.goodhealthtpa.in/Provider/ProviderLogin.aspx'
        

    def login(self):
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID,'txtUsrName')))
            username = self.driver.find_element(By.ID,'txtUsrName')
            username.send_keys(self.user_name) # User name
            password = self.driver.find_element(By.ID,'txtPassword')
            password.send_keys(self.password) # Password 
            self.self.driver.find_element(By.ID,'btnLogin').click() #login
        except Exception as e:
            print(e)

    def navigate(self):
        try:
            self.driver.get('https://webace.goodhealthtpa.in/Provider/ProviderDownloadMIS.aspx')
        except Exception as e:
            print(e)


    def download(self):
        try:
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
        except Exception as e:
            print (e)

@frappe.whitelist()
def initiator():
    GoodHealthDownloader().process()