import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from twocaptcha import TwoCaptcha
from selenium.webdriver.support.ui import WebDriverWait

class CarehealthDownloader(SeleniumDownloader):

    def check_captcha_value(self):
        try:
            message = self.min_wait.until(EC.presence_of_element_located((By.ID, 'Capitchaerror'))).text
            if message == 'Invalid Captcha':
                return False
            return True
        except:
            return True

    def check_login_status(self):
        try:
            if self.check_captcha_value() == False:
                if self.enable_captcha_api == 1:
                    solver = TwoCaptcha(self.captcha[1])
                    solver.report(self.captcha[0]['captchaId'], False)
                return self.captcha_alert
            message = self.min_wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='col-sm-12 col-lg-12' and @style='color:red;']"))).text
            if message == 'Invalid Username or Password':
                return False
            return True if self.login_url != self.driver.current_url else False
        except:
            return True if self.login_url != self.driver.current_url else False

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID, 'UserName'))).send_keys(self.user_name)
        self.wait.until(EC.visibility_of_element_located((By.ID, 'Password'))).send_keys(self.password)
        #captcha bypass
        if self.enable_captcha_api ==1:
            captcha_div = self.wait.until(EC.visibility_of_element_located((By.ID, 'CaptchaText')))
            sitekey = captcha_div.get_attribute('data-sitekey')
            self.captcha = self.get_captcha_value(captcha_type="ReCaptcha", sitekey=sitekey)
            g_recaptcha_response = self.driver.find_element(By.ID, 'g-recaptcha-response')
            self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.resize = 'both';",g_recaptcha_response)
            g_recaptcha_response.send_keys(self.captcha[0]['code'])
        else:
            time.sleep(self.max_wait_time)
        self.login_url = self.driver.current_url
        self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-primary'))).click()

    def navigate(self):
        modal = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "modal-content")))
        cancel_button = modal.find_element(By.XPATH, ".//button[contains(text(),'Cancel')]")
        cancel_button.click()

    def download_from_web(self):
        main_menu = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Payment Status')]")))
        main_menu.click()
        sub_menu = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Paid')]")))
        sub_menu.click()
        self.wait.until(EC.element_to_be_clickable((By.ID, "btnGenerateRE"))).click()
        time.sleep(10)