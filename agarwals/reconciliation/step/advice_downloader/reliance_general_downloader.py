import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import Select


class RelianceGeneralDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def login(self):
        self.driver.maximize_window()
        username = self.wait.until(EC.presence_of_element_located((By.ID, 'txtUsername')))
        pwd = self.wait.until(EC.presence_of_element_located((By.ID, 'txtPassword')))
        username.sendkeys(self.user_name)
        pwd.sendkeys(self.password)
        captcha_img = self.wait.until(EC.presence_of_element_located((By.ID,'captchaImage')))
        if captcha_img:
            self.get_captcha_image(captcha_img)
            captcha_value = self.get_captcha_value()
            if captcha_value:
                login_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'btnLogin')))
                login_button.click()
                time.sleep(5)
                try:
                    error = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                         "//div[@class='mandatory' and @id='divErrorMessage']/p[contains(text(),'Invalid captcha')]")))
                    if error:
                        self.update_tpa_reference("Retry")
                        self.raise_exception(" Invalid Captcha ")
                except:
                    pass

            else:
                self.update_tpa_reference("Retry")
                self.raise_exception(" NO Captcha value Found")
        else:
            self.raise_exception(" NO Captcha Image Found ")

    def navigate(self):
        menu_icon = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a > img[src="/Content/Images/List-View.png"]')))
        parent_link = menu_icon.find_element(By.XPATH, "..")
        parent_link.click()
        time.sleep(2)
        ActionChains(self.driver).move_to_element(parent_link).perform()
        main_menu_present = self.wait.until(EC.presence_of_element_located((By.ID, 'mainMenu')))
        self.wait.until(EC.visibility_of(main_menu_present))
        portal_report_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//li[@class="PortalReportMenu "]/a[@class="PortalReport"]')))
        portal_report_link.click()
        time.sleep(2)
        menu_second_link = self.driver.find_element(By.XPATH, '//a[text()="MIS REPORTS - DASHBOARD"]')
        menu_second_link.click()
        time.sleep(2)

    def download_from_web(self):
        from_date = self.from_date.strftime('%d/%B/%Y')
        to_date = self.to_date.strftime('%d/%B/%Y')
        input_element = self.driver.find_element(By.ID, "misDashBoardFrom")
        input_element.send_keys(from_date)
        input_element = self.driver.find_element(By.ID, "misDashBoardTo")
        input_element.send_keys(to_date)
        dropdown_element = Select(self.driver.find_element(By.ID, "ddlAppliedToDashboard"))
        dropdown_element.select_by_visible_text("Date of Admission")
        dropdown_element = Select(self.driver.find_element(By.ID, "ddlReportTypeDashBoard"))
        dropdown_element.select_by_visible_text("Payment")
        submit_button = self.driver.find_element(By.ID, "DashBoardReportRequest")
        submit_button.click()
        time.sleep(5)
        table = self.wait.until(EC.presence_of_element_located((By.ID,
                                                           'PaymentReportTbl')))
        if table:
            self.extract_table_data("PaymentReportTbl")
        time.sleep(5)



