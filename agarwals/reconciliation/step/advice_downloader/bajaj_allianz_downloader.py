from selenium.common import TimeoutException
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

    def is_invalid_captcha(self):
        try:
            alert = self.min_wait.until(EC.alert_is_present())
            if alert.text == "enter valid captcha code":
                if self.enable_captcha_api == 1:
                    solver = TwoCaptcha(self.captcha_api[1])
                    solver.report(self.captcha_api[0]['captchaId'], False)
                return True
            return False
        except TimeoutException:
            return False
        except Exception as e:
            return e

    def check_login_status(self):
        is_invalid = self.is_invalid_captcha()
        if is_invalid == True:
            return self.captcha_alert
        elif is_invalid == False:
            try:
                message = self.min_wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'message-text text-danger'))).text
                if message == "Invalid username or password":
                    return False
            except:
                return True
        else:
            return is_invalid

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID, 'username'))).send_keys(self.user_name)
        self.wait.until(EC.visibility_of_element_located((By.ID, 'password'))).send_keys(self.password)
        captcha_img = self.wait.until(EC.visibility_of_element_located((By.ID, 'valicode')))
        if captcha_img:
            self.get_captcha_image(captcha_img)
            self.captcha_api = self.get_captcha_value(captcha_type="Normal Captcha")
            captcha_code = self.captcha_api[0]['code'] if self.enable_captcha_api == 1 else self.captcha_api
            self.wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@placeholder='please enter captcha']"))).send_keys(captcha_code)
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.btn.bg-orange.btn-block[type='submit']"))).click()
        else:
            self.raise_exception("Captcha ID NOT FOUND")

    def navigate(self):
        self.wait.until(EC.element_to_be_clickable((By.ID, 'payments'))).click()
        self.wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT,"BAJAJ"))).click()

    def download_from_web(self):
        download_button = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/button/button')))
        self.actions.move_to_element(download_button).click().perform()
        time.sleep(10)
