import frappe
from agarwals.settlement_advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class StarHealthDownloader(SeleniumDownloader):
    def __init__(self):
        super().__init__()
        self.portal = "Star Health"
        self.url = "https://spp.starhealth.in/"

    def login(self):
        print("Hello")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[ng-model="user.username"]')))
        user_name = self.driver.find_element(By.CSS_SELECTOR, 'input[ng-model="user.username"]')
        password = self.driver.find_element(By.CSS_SELECTOR, 'input[ng-model="user.password"]')
        sign_in_button = self.driver.find_element(By.CLASS_NAME, "btn.btn-primary.btn-sh")
        user_name.send_keys(self.user_name)
        password.send_keys(self.password)
        sign_in_button.click()
        print("Logged IN")

    def navigate(self):
        self.wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Dashboard")))
        dashboard = self.driver.find_element(By.LINK_TEXT, "Dashboard")
        dashboard.click()
        print("Navigated")

    def download(self):
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "bx.has-link.bg5.ng-scope")))
        settled_card = self.driver.find_element(By.CLASS_NAME, "bx.has-link.bg5.ng-scope")
        if 'Cashless claims settled' not in settled_card.get_attribute('innerHTML'):
            return False
        actions = ActionChains(self.driver)
        actions.move_to_element(settled_card).perform()
        self.wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Request report")))
        request_report = self.driver.find_element(By.LINK_TEXT, "Request report")
        request_report.click()
        time.sleep(10)
        print("Done")
        return True

@frappe.whitelist()
def initiator():
    StarHealthDownloader().process()