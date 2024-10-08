import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from selenium.common.exceptions import TimeoutException
import time


class MdIndiaOnlineDownloader(SeleniumDownloader):

    def check_login_status(self) ->bool | str :
        try:
            message = self.min_wait.until(EC.visibility_of_element_located((By.ID,'ctl00_ContentPlaceHolder1_lblMsg'))).text
            if message.strip() == 'Invalid Provider Code':
                return False
            elif message.strip() == 'Enter Valid Captcha.':
                if self.enable_captcha_api == 1:
                    solver = TwoCaptcha(self.captcha_code[1])
                    solver.report(self.captcha_code[0]['captchaId'], False)
                return self.captcha_alert
            else:
                return True
        except TimeoutException:
            return True
        except Exception as e:
            raise Exception(e)


    def login(self) -> None:
        self.wait.until(EC.visibility_of_element_located((By.ID,'ctl00_ContentPlaceHolder1_txtProviderCode'))).send_keys(self.user_name)
        captcha_img = self.wait.until(EC.visibility_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_ImageProvider')))
        if captcha_img:
            self.get_captcha_image(captcha_img)
            captcha_code = self.get_captcha_value(captcha_type="Normal Captcha")
            if captcha_code:
                self.captcha_code = captcha_code[0]['code'] if self.enable_captcha_api == 1 else captcha_code
                self.wait.until(EC.visibility_of_element_located((By.ID,'ctl00_ContentPlaceHolder1_txtProviderCaptchaCode'))).send_keys(self.captcha_code)
                self.wait.until(EC.element_to_be_clickable((By.ID,'ctl00_ContentPlaceHolder1_btnSubmit'))).click()
            else:
                raise ValueError("Captcha code is Not Found")
        else:
            raise FileNotFoundError("Captcha Image Not Found")

    def navigate(self) -> None:
        self.wait.until(EC.element_to_be_clickable((By.ID,'ctl00_Menu2_m3'))).click()
        self.wait.until(EC.element_to_be_clickable((By.ID,'ctl00_Menu2_m3_m3'))).click()

    def download_from_web(self) -> None:
        from_date = self.wait.until(EC.element_to_be_clickable((By.ID,'ctl00_ContentPlaceHolder2_SearchControl1_txtFromDate')))
        from_date.send_keys(self.from_date.strftime("%d/%m/%Y"))
        to_date = self.wait.until(EC.visibility_of_element_located((By.ID,'ctl00_ContentPlaceHolder2_SearchControl1_txtToDate')))
        to_date.send_keys(self.to_date.strftime("%d/%m/%Y"))
        self.wait.until(EC.element_to_be_clickable((By.ID,'btnExport'))).click()
        time.sleep(10)
        self.wait.until(EC.visibility_of_element_located((By.ID,'ctl00_lbtnLogOut'))).click()







