import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import TimeoutException,NoSuchElementException
from selenium.webdriver.common.by import By
import time
from twocaptcha import TwoCaptcha

class VidalHealthDownloader(SeleniumDownloader):

    def is_invalid_captcha(self):
        try:
            message = self.min_wait.until(EC.visibility_of_element_located((By.XPATH,'//div[@class="c_popUps"]/p[text()="Captcha not Matched"]')))
            if self.enable_captcha_api == 1:
                solver = TwoCaptcha(self.response[1])
                solver.report(self.response[0]['captchaId'], False)
            return True if message else False
        except TimeoutException:
            return False
        except Exception as e:
            raise Exception(e)

    def check_login_status(self):
        is_invalid = self.is_invalid_captcha()
        if is_invalid == True:
            return self.captcha_alert
        try:
            messages = self.min_wait.until(EC.visibility_of_all_elements_located((By.TAG_NAME,'p')))
            for message in messages:
                if message.text == "Dear Customer, your username/password does not match with our database, please confirm the details.":
                    return False
                else:
                    return str(messages)
        except TimeoutException:
            return True
        except Exception as e:
            raise Exception(e)

    def login(self):
        self.wait.until(EC.visibility_of_element_located((By.ID,'hosUserID'))).send_keys(self.user_name)
        self.wait.until(EC.visibility_of_element_located((By.ID, 'hosPassword'))).send_keys(self.password)
        if self.is_captcha == 1:
            captcha_image_element = self.wait.until(EC.visibility_of_element_located((By.XPATH, "//img[@alt='Captcha']")))
            if captcha_image_element:
                self.get_captcha_image(captcha_image_element)
                self.response = self.get_captcha_value(captcha_type="Normal Captcha")
                if self.response:
                    captcha_value = self.response[0]['code'] if self.enable_captcha_api == 1 else self.response
                    self.wait.until(EC.visibility_of_element_located((By.ID,'inputUsernameEmail'))).send_keys(captcha_value)
                else:
                    raise ValueError("Captcha value Not Found")
            else:
                raise NoSuchElementException('Captcha image element not available')
        self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'vd-btn-primary'))).click()



    def navigate(self):
        time.sleep(5)
        self.driver.execute_script("onSetSubLinks('reports','reports');")

    def download_from_web(self,temp_from_date=None,temp_to_date=None):
        formated_from_date = self.from_date.strftime("%d/%m/%Y") if temp_from_date is None else temp_from_date.strftime("%d/%m/%Y")
        formated_to_date = self.to_date.strftime("%d/%m/%Y") if temp_to_date is None else temp_to_date.strftime("%d/%m/%Y")
        from_date = self.wait.until(EC.visibility_of_element_located((By.ID,'datetimepicker4')))
        to_date = self.wait.until(EC.visibility_of_element_located((By.ID,'datetimepicker5')))
        from_date.click()
        self.driver.execute_script("arguments[0].value = '';", from_date)
        from_date.send_keys(formated_from_date)
        to_date.click()
        self.driver.execute_script("arguments[0].value = '';", to_date)
        to_date.send_keys(formated_to_date)
        self.driver.find_element(By.CLASS_NAME,'vd-btn-primary').click()
        time.sleep(10)

    def download_from_web_with_date_range(self,temp_from_date,temp_to_date,logout):
        self.download_from_web(temp_from_date,temp_to_date)

        
