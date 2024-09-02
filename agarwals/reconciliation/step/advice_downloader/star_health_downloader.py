import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class StarHealthDownloader(SeleniumDownloader):

    def check_login_status(self):
        try:
            message = self.min_wait.until(EC.visibility_of_element_located((By.ID, 'loginMessage'))).text
            if message in ['User not found','Wrong password']:
                return False
            else:
                return message
        except:
            return True
    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[ng-model="user.username"]'))).send_keys(self.user_name)
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[ng-model="user.password"]'))).send_keys(self.password)
        self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"btn.btn-primary.btn-sh"))).click()

    def navigate(self):
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Dashboard"))).click()

    def download_from_web(self):
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "bx.has-link.bg5.ng-scope")))
        settled_card = self.driver.find_element(By.CLASS_NAME, "bx.has-link.bg5.ng-scope")
        if 'Cashless claims settled' not in settled_card.get_attribute('innerHTML'):
            self.raise_exception("Cashless claims settled is not in the HTML element")
        self.actions.move_to_element(settled_card).perform()
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Request report"))).click()
        time.sleep(15)