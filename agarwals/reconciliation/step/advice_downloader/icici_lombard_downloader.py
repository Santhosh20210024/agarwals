import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from twocaptcha import TwoCaptcha
import os

class ICICLombardDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)
        
    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID, 'username')))
        self.driver.find_element(By.ID,'username').send_keys(self.user_name)  #Username
        self.driver.find_element(By.ID,'password').send_keys(self.password) #password
        # captcha = self.driver.find_element(By.XPATH,"//h5[@style='font-size:20px;color:red;user-select:none']").get_attribute("innerHTML")
        captcha = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//img[@title="Captcha"]')))
        if captcha:
            self.get_captcha_image(captcha)
            captcha_api = self.get_captcha_value(captcha_type="Normal Captcha")
            a = captcha_api[0]['code'] if self.enable_captcha_api == 1 else captcha_api

            if a != None:
                self.driver.find_element(By.ID, 'clientCaptcha').send_keys(a)
                self.driver.find_element(By.ID, 'btnLogin').click()
                try:
                    modal = self.wait.until(
                        EC.presence_of_element_located((By.ID, 'simplemodal-container'))
                    )
                    undefined_link = modal.find_element(By.XPATH, "//a[@href='/undefined']//span[text()='undefined']")
                    if undefined_link.text == "undefined":
                       solver = TwoCaptcha(captcha_api[1])
                       solver.report(captcha_api[0]['captchaId'], False)
                       cancel_button = modal.find_element(By.XPATH, "//input[@type='button' and @value='Cancel']")
                       cancel_button.click()
                       self.update_tpa_reference("Retry")
                except Exception as e:
                    pass

            else:
                self.update_tpa_reference("Retry")
                self.raise_exception("No Captcha Value Found")
        else:
            self.raise_exception(" No Captcha Image Found ")


    def navigate(self):
        try:
            time.sleep(5)  
            link =self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT,'IPD MIS')))
            link.click()
        except Exception as E:
            try:
                self.wait.until(EC.alert_is_present())
                alert = self.driver.switch_to.alert
                alert.accept()
                link =self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'IPD MIS')))
                link.click()
            except Exception as error:
                try:
                    link =self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT,'IPD MIS')))
                    link.click()
                except Exception as e:
                    self.raise_exception(' navigation Error ') 

    def download_from_web(self):
        formated_from_date=self.from_date.strftime("%d/%m/%Y")
        formated_to_date = self.to_date.strftime("%d/%m/%Y")
        self.wait.until(EC.visibility_of_element_located((By.ID,'txtFromDate')))
        from_date = self.driver.find_element(By.ID,"txtFromDate")
        self.driver.execute_script("arguments[0].removeAttribute('readonly')", from_date)
        from_date.clear()
        from_date.send_keys(formated_from_date)
        to_date  = self.driver .find_element(By.ID,'txtToDate')
        self.driver.execute_script("arguments[0].removeAttribute('readonly')",to_date)
        to_date.send_keys(formated_to_date)
        self.driver.find_element(By.ID, 'rdoBoth').click()
        self.driver.find_element(By.ID, 'btnGenerateRequest').click()
        time.sleep(5)
