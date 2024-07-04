import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys
import time


class HeritageDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,"txtEmail"))).send_keys(self.user_name)
        self.wait.until(EC.visibility_of_element_located((By.ID, "txtPassword"))).send_keys(self.password)
        self.wait.until(EC.element_to_be_clickable((By.ID, 'btnSubmit'))).click()

    def navigate(self):
        from_date = self.from_date.strftime("%d/%m/%Y")
        to_date = self.to_date.strftime("%d/%m/%Y")
        self.wait.until(EC.element_to_be_clickable((By.ID, 'a_divHospOverView'))).click()
        self.wait.until(EC.element_to_be_clickable((By.ID,"ContentPlaceHolder1_btnClaimSettledForTheYear"))).click()
        actions = ActionChains(self.driver)
        self.wait.until(EC.visibility_of_element_located((By.ID,"ContentPlaceHolder1_txtDOAFrom"))).send_keys(from_date)
        self.wait.until(EC.visibility_of_element_located((By.ID,"ContentPlaceHolder1_txtDOATo"))).send_keys(to_date)
        actions.send_keys(Keys.ENTER)
        actions.perform()

    def download_from_web(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,"ContentPlaceHolder1_btnSearch"))).click()
        time.sleep(10)

