import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from twocaptcha import TwoCaptcha
from selenium.webdriver.support.ui import WebDriverWait

class CarehealthDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID, 'UserName')))
        self.driver.find_element(By.ID, 'UserName').send_keys(self.user_name)  # Username
        self.driver.find_element(By.ID, 'Password').send_keys(self.password)
        prv_url = self.driver.current_url
        #captcha bypass
        if self.enable_captcha_api ==1:
            captcha_div = self.driver.find_element(By.ID, 'CaptchaText')
            sitekey = captcha_div.get_attribute('data-sitekey')
            captcha = self.get_captcha_value(captcha_type="ReCaptcha", sitekey=sitekey)
            g_recaptcha_response = self.driver.find_element(By.ID, 'g-recaptcha-response')
            self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.resize = 'both';",g_recaptcha_response)
            g_recaptcha_response.send_keys(captcha[0]['code'])
        else:
            time.sleep(self.max_wait_time)
        self.driver.find_element(By.CLASS_NAME, 'btn-primary').click()
        #Check Invalid captcha or user
        try:
            invalid_captcha = WebDriverWait(self.driver,  10).until(EC.presence_of_element_located((By.ID, 'Capitchaerror')))
            if prv_url == self.driver.current_url:
                if invalid_captcha.text:
                    solver = TwoCaptcha(captcha[1])
                    solver.report(captcha[0]['captchaId'], False)
                    self.update_retry() if self.enable_captcha_api == 1 else self.update_tpa_reference("Retry")
                    self.raise_exception('Invalid Captcha')
                else:
                   self.raise_exception('Invalid USER')
        except Exception as e:
            if len(e.args) ==0:
                pass
            elif e.args[0] in ['Invalid Captcha', 'INVALID USER']:
                    self.raise_exception(e.args[0])
            else:
                pass


    def navigate(self):
        modal = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "modal-content")))
        # ok_button = modal.find_element(By.XPATH, ".//button[contains(text(),'OK')]")
        cancel_button = modal.find_element(By.XPATH, ".//button[contains(text(),'Cancel')]")
        cancel_button.click()


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