import frappe
import pandas as pd
import requests
from agarwals.settlement_advice_downloader.downloader import Downloader

class VitryaDownloader(Downloader):
    def __init__(self,tpa_name,branch_code,last_executed_time):
        self.tpa=tpa_name
        self.branch_code=branch_code
        self.last_executed_time=last_executed_time
        Downloader.__init__(self)

    def set_username_and_password(self):
        credential_doc = frappe.db.get_list("TPA Login Credentials", filters={"branch_code":['=',self.branch_code],"tpa":['=',self.tpa]},fields="*")
        if credential_doc:
            self.user_name = credential_doc[0].user_name
            self.password = credential_doc[0].encrypted_password
        else:
            self.log_error('TPA Login Credentials',None,"No Credential for the given input")

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