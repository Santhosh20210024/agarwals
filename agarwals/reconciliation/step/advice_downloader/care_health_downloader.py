import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time


class CarehealthDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID, 'UserName')))
        self.driver.find_element(By.ID, 'UserName').send_keys(self.user_name)  # Username
        self.driver.find_element(By.ID, 'Password').send_keys(self.password)  # password
        time.sleep(self.max_wait_time)
        self.driver.find_element(By.CLASS_NAME, 'btn-primary').click()
    def navigate(self):
        modal = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "modal-content")))
        # ok_button = modal.find_element(By.XPATH, ".//button[contains(text(),'OK')]")
        cancel_button = modal.find_element(By.XPATH, ".//button[contains(text(),'Cancel')]")
        cancel_button.click()
        time.sleep(5)

    def download_from_web(self):
        main_menu = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Payment Status')]")))
        main_menu.click()
        sub_menu = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Paid')]")))
        sub_menu.click()
        export_button = self.wait.until(EC.element_to_be_clickable((By.ID, "btnGenerateRE")))
        export_button.click()
        time.sleep(5)

