import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select
from datetime import datetime

from selenium.webdriver.common.keys import Keys
import time


class CholasDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)
    def login(self):
        self.driver.find_element(By.XPATH, "//input[@class='form-control input-login ng-untouched ng-pristine ng-invalid' and @formcontrolname='UserName' and @autocomplete='off' and @required='']").send_keys(self.user_name)
        self.driver.find_element(By.XPATH,"//input[@class='form-control input-login ng-untouched ng-pristine ng-invalid' and @formcontrolname='PassWord' and @type='password' and @autocomplete='off' and @required='']").send_keys(self.password)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn login-btn']"))) .click()
        try:
            invalid_message = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "p.ng-star-inserted")))
            if invalid_message.text == "Invalid User Name or Password":
                print("Invalid username or password.")
                print(invalid_message.text)
                self.raise_exception("Invalid username or password.")
        except:
            pass

    def check_date_type(self,date):
        if isinstance(date, str):
            self.date_time = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            self.date_time =date
        return self.date_time
    def navigate(self):

        payment_status_link = self.wait.until(EC.visibility_of_element_located((By.XPATH, "//span[@class='sidemenu-txt' and text()='Payment Status']")))
        payment_status_link.click()



        select_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@formcontrolname='type']")))

        select = Select(select_element)

        select.select_by_value("Paid Claims")
        # if isinstance(self.from_date, str):
        #     self.from_date_date_time = datetime.strptime(self.from_date, '%Y-%m-%d').date()
        # else:
        #     self.from_date_date_time = self.from_date
        #
        # if isinstance(self.to_date, str):
        #     self.to_date_date_time = datetime.strptime(self.to_date, '%Y-%m-%d').date()
        # else:
        #     self.to_date_date_time = self.to_date
        self.from_date_date_time = self.check_date_type(self.from_date)
        self.to_date_date_time = self.check_date_type(self.to_date)


        self.from_date = self.from_date_date_time.strftime('%Y-%m-%d')
        self.to_date = self.to_date_date_time.strftime('%Y-%m-%d')

        from_date = self.wait.until(EC.visibility_of_element_located((By.ID, "mat-input-1")))

        self.driver.execute_script("arguments[0].removeAttribute('class')", from_date)
        from_date.send_keys(self.from_date)

        to_date = self.wait.until(EC.visibility_of_element_located((By.ID, "mat-input-2")))
        self.driver.execute_script("arguments[0].removeAttribute('class')", to_date)
        to_date.send_keys(self.to_date)

        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".btn.btn-blue"))).click()
    def download_from_web(self):
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@value='Export to Excel']"))).click()
        time.sleep(10)




