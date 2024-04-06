import frappe
from agarwals.settlement_advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class StarHealthDownloader(SeleniumDownloader):
    def __init__(self,tpa_name,branch_code,last_executed_time):
        self.tpa=tpa_name
        self.branch_code=branch_code
        self.last_executed_time=last_executed_time
        SeleniumDownloader.__init__(self)

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[ng-model="user.username"]')))
        user_name = self.driver.find_element(By.CSS_SELECTOR, 'input[ng-model="user.username"]')
        password = self.driver.find_element(By.CSS_SELECTOR, 'input[ng-model="user.password"]')
        sign_in_button = self.driver.find_element(By.CLASS_NAME, "btn.btn-primary.btn-sh")
        user_name.send_keys(self.user_name)
        password.send_keys(self.password)
        sign_in_button.click()
        
    def navigate(self):
        time.sleep(5)
        self.wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Dashboard")))
        dashboard = self.driver.find_element(By.LINK_TEXT, "Dashboard")
        dashboard.click()
        

    def download_from_web(self):
        time.sleep(5)
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "bx.has-link.bg5.ng-scope")))
        settled_card = self.driver.find_element(By.CLASS_NAME, "bx.has-link.bg5.ng-scope")
        if 'Cashless claims settled' not in settled_card.get_attribute('innerHTML'):
            self.raise_exception("Cashless claims settled is not in the HTML element")
        actions = ActionChains(self.driver)
        actions.move_to_element(settled_card).perform()
        self.wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Request report")))
        request_report = self.driver.find_element(By.LINK_TEXT, "Request report")
        request_report.click()
        time.sleep(10)