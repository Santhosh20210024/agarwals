import frappe
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import Select



class ProviderIhxDownloader(SeleniumDownloader):
    def check_login_status(self)->bool:
        try:
            error_message = self.min_wait.until(EC.visibility_of_element_located((By.XPATH, "//span[@class='message-text']"))).text
            if "Incorrect username" in error_message or "Incorrect password" in error_message:
                return False
        except :
            return True

    def login(self):
        username = self.wait.until(EC.visibility_of_element_located((By.ID, 'login-form_username')))
        pwd = self.driver.find_element(By.ID, 'login-form_password')
        username.send_keys(self.user_name)
        pwd.send_keys(self.password)
        login_button = self.driver.find_element(By.XPATH, "//button[@class='ant-btn ant-btn-primary login-btn']")
        login_button.click()
        if self.check_login_status() == False:
            raise ValueError("Invalid user name or password")

    def navigate(self):
        try:
            skip = self.min_wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'skip-verification')))
            skip.click()
        except:
            pass
        # Wait for the sidebar to be present
        sidebar = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ant-layout-sider")))
        # Move the mouse cursor over the sidebar to trigger expansion
        action = ActionChains(self.driver)
        action.move_to_element(sidebar).perform()

        # Wait for the sidebar to expand
        self.wait.until(lambda driver: "ant-layout-sider-collapsed" not in sidebar.get_attribute("class"))

        # Wait for the "Reconciliation" li element to be present
        reconciliation_li = self.wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@title='Reconciliation']")))

        # Scroll the element into view if necessary
        self.driver.execute_script("arguments[0].scrollIntoView(true);", reconciliation_li)

        # Wait for the "Reconciliation" span to be clickable
        reconciliation_span = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[@title='Reconciliation']//span[contains(text(), 'Reconciliation')]")))
        reconciliation_span.click()

        # time.sleep(20)

        # Wait for the iframe to be present
        iframe = self.wait.until(EC.visibility_of_element_located((By.XPATH, "//iframe[contains(@src, 'app.powerbi.com')]")))

        # Switch focus to the iframe
        self.driver.switch_to.frame(iframe)
        row_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[row-index='0']")))
        actions = ActionChains(self.driver)
        actions.move_to_element(row_element).perform()

        more_options_button = self.wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "button[data-testid='visual-more-options-btn']")
            )
        )

        # Click the button
        more_options_button.click()
        dropdown_menu = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".pbi-menu-compact")))

        # Locate the "Export data" button using aria-label
        export_data_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".pbi-menu-item-text-container")))
        export_data_button.click()

    def download_from_web(self):
        export_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='export-btn']")))
        export_button.click()
        self.driver.switch_to.default_content()
        time.sleep(10)