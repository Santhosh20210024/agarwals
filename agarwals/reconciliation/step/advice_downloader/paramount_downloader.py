import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class ParamountDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def login(self):
        username = self.wait.until(EC.visibility_of_element_located((By.ID,'txtUserName')))
        username.send_keys(self.user_name)
        pwd = self.wait.until((EC.visibility_of_element_located((By.ID,'txtPassword'))))
        pwd.send_keys(self.password)
        captcha_element = self.driver.find_element(By.ID,'ContentPlaceHolder1_lblStopSpam')
        captcha_text = captcha_element.get_attribute('innerHTML')
        captcha_answer = eval(captcha_text)
        self.driver.find_element(By.ID,"ContentPlaceHolder1_txtCaptcha").send_keys(captcha_answer)
        login_btn = self.driver.find_element(By.ID,"ContentPlaceHolder1_btnLogin")
        login_btn.click()

    def navigate(self):
        self.driver.get("https://provider.paramounttpa.com/PaidClaims.aspx")

    def download_from_web(self,temp_from_date = None, temp_to_date=None):
        formated_from_date=self.from_date.strftime("%d/%m/%Y") if temp_from_date is None else temp_from_date.strftime("%d/%m/%Y")
        formated_to_date = self.to_date.strftime("%d/%m/%Y") if temp_to_date is None else temp_to_date.strftime("%d/%m/%Y")
        from_date = self.wait.until(EC.visibility_of_element_located((By.ID,"dateFrom")))
        from_date.click()
        from_date.clear()
        from_date.send_keys(formated_from_date)
        to_date = self.wait.until(EC.visibility_of_element_located((By.ID,"dateTo")))
        to_date.click()
        to_date.clear()
        to_date.send_keys(formated_to_date)
        self.driver.find_element(By.ID,"ContentPlaceHolder1_btnSubmit").click()
        time.sleep(5)
        export_button = self.wait.until(EC.visibility_of_element_located((By.ID,"ContentPlaceHolder1_btnExport")))
        export_button.click()
        time.sleep(10)

    def download_from_web_with_date_range(self,temp_from_date, temp_to_date,logout):
        self.download_from_web(temp_from_date,temp_to_date)