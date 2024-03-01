import frappe
import pandas as pd
import requests
from datetime import datetime,timedelta
from agarwals.settlement_advice_downloader.downloader import Downloader

class StarHealthDownloader(Downloader):
    def __init__(self):
        super().__init__()
        self.portal = "Star Health"
        self.user_name = None
        self.password = None
    def get_user_credentials_tpa_and_branch(self):
        tpa_credential_doc = frappe.get_list("TPA Login Credentials", filters={'portal': self.portal}, fields='*')
        time_exc = datetime.now()
        for tpa_credential in tpa_credential_doc:
            if tpa_credential.exectution_time:
                if (time_exc - timedelta(minutes=2)).time() < tpa_credential.exectution_time.time() <= time_exc.time():
                    return tpa_credential['branch_code'], tpa_credential['tpa'], tpa_credential['user_name'], tpa_credential['encrypted_password']
        return None, None, None, None

    def get_access_token_and_hosp_id(self):
        login_url = "https://spp-api.starhealth.in/Provider/Login"
        login_header = {'accept':'application/json, text/plain, */*','content-type':'application/json;charset=UTF-8'}
        login_body = {"userName":self.user_name,"password":self.password}
        login_response = requests.post(login_url,headers = login_header, json = login_body)
        response_json = login_response.json()
        if login_response.status_code == 200 and response_json['accessToken']:
            return response_json['accessToken'], response_json["hospDetails"]["hospId"]
        return None, None

    def get_response_content(self,access_token,hosp_id):
        download_url = "https://spp-api.starhealth.in/Provider/Search/DownloadDashboardReport"
        download_header = {'accept':'application/json, text/plain, */*','content-type':'application/json;charset=UTF-8','accesstoken':access_token}
        download_body = {"providerId":hosp_id,"payerId":1005326,"preferedDashBoard":"settlement"}
        download_response = requests.post(download_url, headers=download_header, json=download_body)
        if download_response.status_code == 200 and download_response.content:
            return download_response.content
        return None


    def get_content(self):
        access_token, hosp_id = self.get_access_token_and_hosp_id()
        if not access_token:
            self.log_error('TPA Login Credentials', self.user_name, "Access Token is NULL")
            return None
        content = self.get_response_content(access_token,hosp_id)
        if not content:
            return None
        return content

