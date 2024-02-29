import frappe
import pandas as pd
import requests
from agarwals.utils.path_data import PROJECT_FOLDER,HOME_PATH,SHELL_PATH,SUB_DIR
from agarwals.settlement_advice_downloader.downloader import Downloader

class StarHealthDownloader(Downloader):
    def __init__(self, tpa, branch_name):
        super().__init__()
        self.tpa = tpa
        self.branch_name = branch_name

    def get_access_token_and_hosp_id(self, username, password):
        login_url = "https://spp-api.starhealth.in/Provider/Login"
        login_header = {'accept':'application/json, text/plain, */*','content-type':'application/json;charset=UTF-8'}
        login_body = {"userName":username,"password":password}
        login_response = requests.post(login_url,headers = login_header, json = login_body)
        response_json = login_response.json()
        if login_response.status_code == 200 and response_json['access_token']:
            return response_json['access_token'], response_json["hospDetails"]["hospId"]
        return None

    def get_response_content(self,access_token,hosp_id):
        download_url = "https://spp-api.starhealth.in/Provider/Search/DownloadDashboardReport"
        download_header = {'accept':'application/json, text/plain, */*','content-type':'application/json;charset=UTF-8','accesstoken':access_token}
        download_body = {"providerId":hosp_id,"payerId":1005326,"preferedDashBoard":"settlement"}
        download_response = requests.post(download_url, headers=download_header, json=download_body)
        if download_response.status_code == 200 and download_response.content:
            return download_response.content
        return None

    def write_to_file(self,file_name, content):
        if file_name and content:
            with open(file_name, "wb") as file:
                file.write(content)
            shutil.move(file_name,  construct_file_url(self.SITE_PATH, self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0]))
            file=frappe.new_doc("File")
            file.folder = construct_file_url(self.HOME_PATH, self.SUB_DIR[0])
            file.is_private=1
            file.file_url= "/" + construct_file_url(self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0], file_name)
            file.save(ignore_permissions=True)
            self.delete_backend_files(file_path=construct_file_url(self.SITE_PATH, self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0],file_name))
            file_url="/"+construct_file_url(self.SHELL_PATH, file_name)
            frappe.db.commit()
            self.create_fileupload(file_url)

    def content(self,username, password):
        access_token, hosp_id = self.get_access_token_and_hosp_id(username,password)
        if not access_token:
            self.log_error('TPA Login Credentials', self.user_name, "Access Token is NULL")
            return None
        content = self.get_response_content(access_token,hosp_id)
        if not content:
            return None
        return content

