import frappe
from selenium import webdriver
from agarwals.reconciliation.step.advice_downloader.selenium_downloader import SeleniumDownloader
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import os
import time


class CholasPdfDownloader(SeleniumDownloader):
    def __init__(self):
        SeleniumDownloader.__init__(self)
        self.format_file_in_parent = False
        self.settled_claims = 0
    def login(self):
        self. user_name = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@formcontrolname='UserName']"))).send_keys(self.user_name)
        self.password = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@formcontrolname='PassWord' and @type='password']"))).send_keys(self.password)
        login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn login-btn' and text()='LOGIN']")))
        login_button.click()
        
   
    def navigate(self):
        dash_count = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "dash-count")))
        dash_elements = self.driver.find_elements(By.CLASS_NAME, "dash-count")
        claims_submitted =self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dash-box-txt' and text()='Claims Submitted for Payment']")))
        claims_submitted.click()
        self.settled_claims = dash_elements[-1].text
        arrow = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='mat-select-arrow']")))
        arrow.click()
        
    
        option_element = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//span[@class="mat-option-text" and contains(text(), "100")]'))
        )
        option_element.click()
    
    def download_from_web(self):
        td_elements = self.driver.find_elements(By.XPATH, "//td[@class='mat-cell cdk-column-memberID mat-column-memberID ng-star-inserted']")
        c = 0
        for i  in range(int(self.settled_claims)):
            try:
                self.previous_files_count = len(os.listdir(self.download_directory))
                a_tag = td_elements[c].find_element(By.XPATH, ".//a")
                a_tag.click()
                time.sleep(10)
                self.format_downloaded_file()
                c=c+1
                if c == 100:
                    c=0
                    td_elements = self.driver.find_elements(By.XPATH, "//td[@class='mat-cell cdk-column-memberID mat-column-memberID ng-star-inserted']")
                    next_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next page']"))).click()
                time.sleep(2)   
            except Exception as e:
                print(f"Failed to click on member ID link: {e}")  
                
                 
            

    
        
        


       