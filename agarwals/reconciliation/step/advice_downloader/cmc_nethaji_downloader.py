import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert
from twocaptcha import TwoCaptcha





class CMCNethajiEyeFoundationDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)
        self.extract_first_table = True

    def login(self):
        username = self.wait.until(EC.visibility_of_element_located((By.ID, 'txtusername')))
        pwd = self.driver.find_element(By.ID, 'txtpassword')

        username.send_keys(self.user_name)
        pwd.send_keys(self.password)
        time.sleep(20)
        captcha_img = self.wait.until(EC.visibility_of_element_located((By.ID, 'imgCaptcha')))
        if captcha_img:
            self.get_captcha_image(captcha_img)
            captcha_api = self.get_captcha_value(captcha_type="Normal Captcha")
            captcha_code = captcha_api[0]['code'] if self.enable_captcha_api == 1 else captcha_api
            if captcha_code != None:
                captcha_entry = self.wait.until(EC.visibility_of_element_located((By.ID, "txtCaptcha")))
                captcha_entry.send_keys(captcha_code)
                self.wait.until(EC.element_to_be_clickable((By.ID, 'Submit1'))).click()
                try:
                    time.sleep(2)
                    alert = Alert(self.driver)
                    if alert.text == "Please Enter Correct Captcha":
                        if self.enable_captcha_api == 1:
                            solver = TwoCaptcha(captcha_api[1])
                            solver.report(captcha_api[0]['captchaId'], False)
                            self.update_retry()
                        else:
                            self.update_tpa_reference("Retry")

                        self.raise_exception("Invalid Captcha")
                except:
                    pass
            else:
                self.update_retry()
                if self.enable_captcha_api == 0:
                    self.update_tpa_reference("Retry")
                self.raise_exception("Invalid Captcha")
        else:
            self.raise_exception("Captcha ID NOT FOUND")

    def navigate(self):
        preauth_tab = self.wait.until(EC.element_to_be_clickable((By.ID, "a_preauth")))
        preauth_tab.click()
        time.sleep(2)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        isprint_mis_link = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, "//a[@id='ctl00_a_mis']/span[text()='iSprint MIS']")))
        isprint_mis_link.click()
        iframe = self.wait.until(EC.visibility_of_element_located((By.NAME, '_ddajaxtabsiframe-countrydivcontainer')))
        self.driver.switch_to.frame(iframe)
        Request_type_dropdown = self.wait.until(EC.visibility_of_element_located((By.ID, 'RequestTypeDDL')))
        select_request_type = Select(Request_type_dropdown)
        select_request_type.select_by_value('Claims')
        time.sleep(10)
        satus_dropdown = self.wait.until(EC.visibility_of_element_located((By.ID, 'statusDDL')))
        select_status = Select(satus_dropdown)
        select_status.select_by_value('8')


    def download_from_web(self,temp_from_date=None,temp_to_date=None):
        formated_from_date = self.from_date.strftime("%d/%m/%Y") if temp_from_date is None else temp_from_date.strftime("%d/%m/%Y")
        formated_to_date = self.to_date.strftime("%d/%m/%Y") if temp_to_date is None else temp_to_date.strftime("%d/%m/%Y")
        txt_from_date = self.wait.until(EC.visibility_of_element_located((By.ID, 'txtFromDate')))
        txt_from_date.click()
        txt_from_date.clear()
        txt_from_date.send_keys(formated_from_date)
        txt_to_date = self.wait.until(EC.visibility_of_element_located((By.ID, 'txtToDate')))
        txt_to_date.click()
        txt_to_date.clear()
        txt_to_date.send_keys(formated_to_date)
        generate_mis_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'BTNGenerateMIS')))
        generate_mis_button.click()
        excel_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'ExcelImageBtn')))
        excel_button.click()
        time.sleep(10)


    def logout(self):
        self.driver.switch_to.default_content()
        home_tab = self.wait.until(EC.element_to_be_clickable((By.ID, 'a_ppnhome')))
        home_tab.click()
        logout_link = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Log-Out')))
        logout_link.click()
    def download_from_web_with_date_range(self,temp_from_date,temp_to_date,logout):
        self.download_from_web(temp_from_date,temp_to_date)
        if logout == 1:
            self.logout()