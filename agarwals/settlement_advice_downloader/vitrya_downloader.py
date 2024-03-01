import frappe
import pandas as pd
import requests
from datetime import datetime,timedelta
from agarwals.settlement_advice_downloader.downloader import Downloader

class VitryaDownloader(Downloader):
    def __init__(self):
        super().__init__()
        self.portal = "Vitraya"
        self.user_name = None
        self.password = None

    def get_user_credentials_tpa_and_branch(self):
        tpa_credential_doc = frappe.get_list("TPA Login Credentials", filters={'portal': self.portal}, fields='*')
        time_exc = datetime.now()
        for tpa_credential in tpa_credential_doc:
            if tpa_credential.exectution_time:
                if (time_exc - timedelta(minutes=2)).time() < tpa_credential.exectution_time.time() <= time_exc.time():
                    return tpa_credential['branch_code'], tpa_credential['tpa'], tpa_credential['user_name'], \
                    tpa_credential['encrypted_password']
        return None, None, None, None

    def get_web_token(self):
        login_url = "https://a2s.starhealth.in/rules-engine/api/v1/user/signin"
        login_header = {'accept':'application/json, text/plain, */*','content-type':'application/json;charset=UTF-8'}
        login_body = {"email":self.user_name,"password":self.password}
        login_response = requests.post(login_url,headers = login_header, json = login_body)
        response_json = login_response.json()
        if login_response.status_code == 200 and response_json['data']['webtoken']['token']:
            print(response_json['data']['webtoken']['token'])
            return response_json['data']['webtoken']['token']
        return None

    def get_response_content(self,web_token):
        download_url = "https://a2s.starhealth.in/rules-engine/api/v1/reports/download/claimsReport"
        download_header = {'accept':'application/json, text/plain, */*','content-type':'application/json;charset=UTF-8', 'X-Auth-Token': web_token, 'X-Client-Platform': 'web'}
        download_params = {'startDate':'2023-04-01','endDate':'2024-02-29'}
        download_response = requests.get(download_url, headers=download_header, params=download_params)
        if download_response.status_code == 200 and download_response.content:
            return download_response.content
        return None


    def get_content(self):
        web_token = self.get_web_token()
        if not web_token:
            self.log_error('TPA Login Credentials', self.user_name, "Web Token is NULL")
            return None
        content = self.get_response_content(web_token)
        if not content:
            return None
        return content