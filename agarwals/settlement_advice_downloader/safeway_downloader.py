import frappe
from agarwals.settlement_advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class SafewayDownloader(SeleniumDownloader):
    def __init__(self):
        super().__init__()
        self.portal = "Safeway"
        self.url = "https://www.safewaytpa.in/Hospitallogin.aspx"

    def login(self):
        self.wait.until(EC.visibility_of_element_located(By.ID, "ctl00_ContentPlaceHolder1_txt_username"))
        username = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txt_username")
        username.send_keys(self.user_name)  # input username
        password = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txt_pwd")
        password.send_keys(self.password)  # input password
        submit = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ImageButton1").click()

    def navigate(self):
        self.wait.until(EC.visibility_of_all_elements_located(By.LINK_TEXT, "Claim MIS"))
        self.driver.find_element(By.LINK_TEXT, "Claim MIS").click()
        from_date = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_DtpFrom_Date5")
        from_date.send_keys('02/12/2023')  # input from date
        to_date = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_Dtpto_Date5")
        to_date.send_keys('31/03/2024')  # input to date
        self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_Button1").click() #submit

    def download(self):
        self.wait.until(EC.visibility_of_element_located,(By.ID, "ctl00_ContentPlaceHolder1_lbltot"))
        record_count = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_lbltot")
        inner_html = record_count.get_attribute("innerHTML")
        if inner_html == 'No Record Found':
            return False
        else:
            self.wait.until(EC.visibility_of_element_located,(By.ID,"ctl00_ContentPlaceHolder1_btnExportInXLS"))
            self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btnExportInXLS").click() #Export
            time.sleep(10)
            return True

@frappe.whitelist()
def initiator():
    SafewayDownloader().process()