import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
import time


class BajajAllianzDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)
    def login(self):
        username = self.wait.until(EC.visibility_of_element_located((By.ID, 'username')))
        username.send_keys(self.user_name)
        self.driver.find_element(By.ID, 'password').send_keys(self.password)
        captcha_img = self.wait.until(EC.visibility_of_element_located((By.ID, 'valicode')))
        if captcha_img:
            self.get_captcha_image(captcha_img)
            captcha = self.get_captcha_value(captcha_type=1)
            print("---------------------------captcha---------------------------",captcha)
            if captcha != None:
                captcha_entry = self.wait.until(
                    EC.visibility_of_element_located((By.XPATH, "//*[@placeholder='please enter captcha']")))
                captcha_entry.send_keys(captcha)
                self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input.btn.bg-orange.btn-block[type='submit']"))).click()
                try:

                    time.sleep(2)
                    alert = Alert(self.driver)
                    if alert.text == "enter valid captcha code":
                        self.update_tpa_reference("Retry")
                except:
                    pass
            else:
                self.update_tpa_reference("Retry")
        else:
            self.log_error('Settlement Advice Downloader UI', self.tpa, "captcha ID NOT FOUND")


    def navigate(self):
        time.sleep(5)
        payments_tab = self.wait.until(EC.visibility_of_element_located((By.ID, 'payments')))
        payments_tab.click()
        paid_claim_details = self.wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT,"BAJAJ")))
        paid_claim_details.click()
        time.sleep(5)

    def download_from_web(self):
        download_button = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/button/button')))
        action_chains = ActionChains(self.driver)
        time.sleep(5)
        action_chains.move_to_element(download_button).click().perform()
        time.sleep(10)
