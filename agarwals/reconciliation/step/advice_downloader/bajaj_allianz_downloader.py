import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
import time
from twocaptcha import TwoCaptcha
import os


class BajajAllianzDownloader(SeleniumDownloader):

    def check_captcha_value(self,captcha_api):
        try:
            self.driver.implicitly_wait(3)
            alert = Alert(self.driver)
            if alert.text == "enter valid captcha code":
                if self.enable_captcha_api == 1:
                    solver = TwoCaptcha(captcha_api[1])
                    solver.report(captcha_api[0]['captchaId'], False)
                else:
                    self.update_tpa_reference("Retry")
                raise ValueError('Invalid Captcha Entry')
        except:
            pass
    def login(self):
        username = self.wait.until(EC.visibility_of_element_located((By.ID, 'username')))
        username.send_keys(self.user_name)
        self.driver.find_element(By.ID, 'password').send_keys(self.password)
        captcha_img = self.wait.until(EC.visibility_of_element_located((By.ID, 'valicode')))
        if captcha_img:
            self.get_captcha_image(captcha_img)
            captcha_api = self.get_captcha_value(captcha_type="Normal Captcha")
            captcha_code = captcha_api[0]['code'] if self.enable_captcha_api == 1 else captcha_api
            if captcha_code != None:
                captcha_entry = self.wait.until(
                    EC.visibility_of_element_located((By.XPATH, "//*[@placeholder='please enter captcha']")))
                captcha_entry.send_keys(captcha_code)
                self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input.btn.bg-orange.btn-block[type='submit']"))).click()
                self.check_captcha_value(captcha_api)
            else:
                if self.enable_captcha_api == 0:
                    self.update_tpa_reference("Retry")
                raise ValueError('No captcha value found')
        else:
                self.raise_exception("Captcha ID NOT FOUND")
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
