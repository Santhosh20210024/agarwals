import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class ParamountDownloader(SeleniumDownloader):

    def check_login_status(self):
        try:
            alter_message = self.min_wait.until(EC.alert_is_present()).text
            if alter_message == 'Invalid User Name/ Password':
                return False
            elif alter_message == 'Invalid Captcha Code':
                return self.captcha_alert
        except:
            return True
    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,'txtUserName'))).send_keys(self.user_name)
        self.wait.until(EC.visibility_of_element_located((By.ID,'txtPassword'))).send_keys(self.password)
        captcha_text = self.wait.until((EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_lblStopSpam')))).get_attribute('innerHTML') # geting captcha as text
        self.wait.until(EC.visibility_of_element_located((By.ID,"ContentPlaceHolder1_txtCaptcha"))).send_keys(eval(captcha_text))
        self.wait.until(EC.element_to_be_clickable((By.ID,"ContentPlaceHolder1_btnLogin"))).click()

    def navigate(self):
        self.driver.get("https://provider.paramounttpa.com/PaidClaims.aspx")

    def download_from_web(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,"dateFrom"))).send_keys(self.from_date.strftime("%d/%m/%Y"))
        self.wait.until(EC.visibility_of_element_located((By.ID,"dateTo"))).send_keys(self.to_date.strftime("%d/%m/%Y"))
        self.wait.until(EC.element_to_be_clickable((By.ID,"ContentPlaceHolder1_btnSubmit"))).click()
        time.sleep(5)
        self.wait.until(EC.element_to_be_clickable((By.ID,"ContentPlaceHolder1_btnExport"))).click()
        time.sleep(10)
