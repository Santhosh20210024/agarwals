import frappe
import requests
from agarwals.settlement_advice_downloader.downloader import Downloader

class StarHealthDownloader(Downloader):
    def __init__(self,tpa_name,branch_code, last_executed_time):
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
            self.log_error('TPA Login Credentials',None,"No Credenntial for the given input")

    def get_access_token_and_hosp_id(self):
        login_url, login_header, login_body, login_params, login_cookies=self.get_meta_data("StarHealthDownloader","login",{"body":[{"{user_name}":self.user_name},{"{password}":self.password}]})
        login_response = requests.post(login_url,headers = login_header, json = login_body)
        response_json = login_response.json()
        if login_response.status_code == 200 and 'accessToken' in response_json:
            return response_json['accessToken'], response_json["hospDetails"]["hospId"]
        return None, None

    def get_response_content(self,access_token,hosp_id):
        download_url, download_header, download_body, download_params, download_cookies=self.get_meta_data("StarHealthDownloader","download",{"header":[{"{access_token}":access_token}]},{"body":[{"{hosp_id}":hosp_id}]})
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

