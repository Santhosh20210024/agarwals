import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import Select
from twocaptcha import TwoCaptcha



class RelianceGeneralDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)


    def login(self):
        username = self.wait.until(EC.presence_of_element_located((By.ID, 'txtUsername')))
        pwd = self.wait.until(EC.presence_of_element_located((By.ID, 'txtPassword')))
        username.send_keys(self.user_name)
        pwd.send_keys(self.password)
        captcha_img = self.wait.until(EC.presence_of_element_located((By.ID,'captchaImage')))
        if captcha_img:
            self.get_captcha_image(captcha_img)
            captcha_api = self.get_captcha_value(captcha_type="Normal Captcha")
            captcha_code = captcha_api[0]['code'] if self.enable_captcha_api == 1 else captcha_api
            if captcha_code != None:
                self.wait.until(EC.visibility_of_element_located((By.ID,"captchaImageText"))).send_keys(captcha_code)
                login_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'btnLogin')))
                login_button.click()
                try:
                    # error = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                    #                                                      "//div[@class='mandatory' and @id='divErrorMessage']/p[contains(text(),'Invalid captcha')]")))
                    error_div = self.driver.find_element(By.ID, "divErrorMessage")
                    error_message = error_div.find_element(By.TAG_NAME, "p").text
                    if "Invalid captcha" in error_message:
                        if self.enable_captcha_api == 1:
                            solver = TwoCaptcha(captcha_api[1])
                            solver.report(captcha_api[0]['captchaId'], False)
                            self.update_retry()
                        else:
                            self.update_tpa_reference("Retry")
                        self.raise_exception("Invalid Captcha")
                except Exception as e:
                    pass
            else:
                self.update_retry()
                if self.enable_captcha_api == 0:
                    self.update_tpa_reference("Retry")
                self.raise_exception("Invalid Captcha")
        else:
            self.raise_exception("Captcha ID NOT FOUND")

    def navigate(self):
        try:
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
        except:
            self.logout()
            self.raise_exception("Navigate Failed")

    def download_from_web(self):
        try:
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
            self.logout()
        except:
            self.logout()
            self.raise_exception("Download Failed")

    def logout(self):
        user_img = self.wait.until(EC.element_to_be_clickable((By.ID, 'imgUser')))
        user_img.click()
        logout_link = self.wait.until(EC.element_to_be_clickable((By.ID, 'lnkLogOutDashboard')))
        logout_link.click()
        confirm_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "confirm"))
        )
        confirm_button.click()




