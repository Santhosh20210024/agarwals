import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
import time


class FHPLDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def login(self):
        self.driver.maximize_window()
        self.wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_txtUserName'))).send_keys(
            self.user_name)
        self.wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_txtPassword'))).send_keys(
            self.password)
        self.driver.find_element(By.ID, 'ContentPlaceHolder1_btnLogin').click()
        time.sleep(5)

    def navigate(self):
        self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_txtDateFrom'))).send_keys(
            self.from_date.strftime("%m/%d/%Y"))
        self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_txtDateTo'))).send_keys(
            self.to_date.strftime("%m/%d/%Y"))
        self.wait.until(EC.visibility_of_element_located((By.NAME, 'ctl00$ContentPlaceHolder1$btnSearch'))).click()
        time.sleep(2)

    def download_from_web(self):
        self.wait.until(EC.visibility_of_element_located((By.ID, 'ContentPlaceHolder1_btnPortToExcel'))).click()
        time.sleep(10)