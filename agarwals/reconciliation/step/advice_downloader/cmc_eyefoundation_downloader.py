import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import Select



class CMCEyeFoundationDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)

    def login(self):
        username = self.wait.until(EC.presence_of_element_located((By.ID, 'txtusername')))
        pwd = self.driver.find_element(By.ID, 'txtpassword')

        username.send_keys("eyefoundation_dmo")
        pwd.send_keys("H_print")
        time.sleep(20)
        login_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'Submit1')))
        login_button.click()

    def navigate(self):
        isprint_mis_link = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//a[@id='ctl00_a_mis']/span[text()='iSprint MIS']")))

        # Click the "Claims" link
        isprint_mis_link.click()
        payment_mis_link = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[@id='a_fm_mis' and @href='../Payer/FM_MIS.aspx']/span[text()='Payment MIS']")))
        payment_mis_link.click()

        # Switch to the iframe
        iframe = self.wait.until(EC.presence_of_element_located((
            By.NAME, '_ddajaxtabsiframe-countrydivcontainer')))
        self.driver.switch_to.frame(iframe)
        # Select "Coimbatore" in the district dropdown
        district_dropdown = self.wait.until(EC.presence_of_element_located((By.ID, 'DdlDistrict')))
        district_dropdown.click()  # Click on the dropdown to open it
        coimbatore_option = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//option[@value='12']")))
        coimbatore_option.click()  # Click on the Coimbatore option

        # Select "COIMBATORE" in the zone dropdown
        zone_dropdown = self.wait.until(EC.presence_of_element_located((By.ID, 'DDLtpaZone')))
        zone_dropdown.click()  # Click on the dropdown to open it
        coimbatore_zone_option = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//option[@value='COIMBATORE']")))
        coimbatore_zone_option.click()  # Click on the COIMBATORE option
        # Find and interact with the date inputs (txtFromDate and txtToDate)
        status_dropdown = self.wait.until(EC.element_to_be_clickable((By.ID, "DdlStatus")))

        # Use the Select class to interact with the dropdown
        select = Select(status_dropdown)

        # Select the option by value
        select.select_by_value("PAID")
        txt_from_date = self.wait.until(EC.presence_of_element_located((By.ID, 'txtFromDate')))
        txt_from_date.send_keys("01/01/2024")  # Enter your desired start date

        txt_to_date = self.wait.until(EC.presence_of_element_located((By.ID, 'txtToDate')))
        txt_to_date.send_keys("29/05/2024")  # Enter your desired end date

    def download_from_web(self):
        generate_button = self.driver.find_element(By.ID, "BTNMIS")

        # Click the button
        generate_button.click()
        table = self.wait.until(EC.visibility_of_element_located((By.ID, "MisGridView")))
        EXCEL_button = self.driver.find_element(By.ID, "ExcelImageBtn")

        # Click the button
        EXCEL_button.click()
        # Now you can interact with elements inside the iframe after setting the date inputs
        # For example, you can find elements and perform actions like clicking buttons or filling forms

        # After interacting with elements inside the iframe, switch back to the default content
        self.driver.switch_to.default_content()
        home_link = self.driver.find_element(By.ID, "a_ppnhome")

        # Click the link
        home_link.click()

    def logout(self):
        logout_link = self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Log-Out")))
        logout_link.click()