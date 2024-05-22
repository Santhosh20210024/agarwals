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
        self.wait.until(EC.presence_of_element_located((By.ID,'txtUserName'))).send_keys(self.user_name)
        self.wait.until(EC.presence_of_element_located((By.ID,'txtPassword'))).send_keys(self.password)
        self.driver.find_element(By.ID,'btnLogIn').click()
        time.sleep(5)

    def navigate(self):
        self.wait.until(EC.element_to_be_clickable((By.ID, 'mnClaimsDashboard'))).click()

    def download_from_web(self):
        count = self.driver.find_element(By.ID,'ContentPlaceHolder1_TabContainer1_tbClaimssettled_lblClaimssettled')
        time.sleep(5)
        if int((count.text).split('(')[1].split(')')[0]) != 0:
            self.extract_table_data('ContentPlaceHolder1_TabContainer1_tbClaimssettled_grdClaimssettled')
        else:
            self.log_error('Settlement Advice Downloader UI', self.tpa, "No Record Found")