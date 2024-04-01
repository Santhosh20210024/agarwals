import requests
from agarwals.settlement_advice_downloader.downloader import Downloader

class ProviderIhx(Downloader):
    def __init__(self,tpa_name,branch_code,last_executed_time):
        self.tpa=tpa_name
        self.branch_code=branch_code
        self.last_executed_time=last_executed_time
        Downloader.__init__(self)
    
    def get_access_token_and_provider_details(self):
        login_url, login_header, login_body, login_params, login_cookies=self.get_meta_data("ProviderIhx","login",{"body":[{"{user_name}":self.user_name},{"{password}":self.password}]})
        login_response = requests.post(login_url,headers=login_header,json=login_body)
        response_json = login_response.json()
        if login_response.status_code == 200 and "accessToken" in response_json:
            return response_json["accessToken"],response_json['userDetail']['profileId'], response_json['providerDetail']['providerId'], response_json['providerDetail']['providerName'], response_json['providerDetail']['providerRohiniCode'], response_json['userDetail']['properties']['MAID']
        return None, None, None, None, None, None
    
    def get_embed_token(self, access_token, profile_id, provider_id, provider_name, rohini_code):
        embed_url, embed_header, embed_body, embed_params, embed_cookies=self.get_meta_data("ProviderIhx","embed",{"header":[{"{access_token}":access_token}],"body":[{"{profile_id}":profile_id},{"{provider_id}":provider_id},{"{provider_name}":provider_name},{"{rohini_code}":rohini_code}]})
        embed_response = requests.post(embed_url,headers=embed_header,json=embed_body)
        response_json = embed_response.json()
        if embed_response.status_code == 200 and 'token' in response_json['embedToken']:
            return response_json['embedToken']['token']
        return None
    
    def get_content_from_site(self, embed_token, ma_id):
        download_url, download_header, download_body, download_params, download_cookies=self.get_meta_data("ProviderIhx","download",{"header":[{"{embed_token}":embed_token}],"body":[{"{ma_id}":ma_id}]})
        download_response = requests.post(download_url,headers=download_header,json=download_body)
        if download_response.status_code != 200:
            return None
        return download_response.content
    
    def get_content(self):
        access_token, profile_id, provider_id, provider_name, rohini_code, ma_id = self.get_access_token_and_provider_details()
        if not access_token:
            self.log_error('TPA Login Credentials', self.user_name, "Access Token is NULL")
            return None
        embed_token = self.get_embed_token(access_token, profile_id, provider_id, provider_name, rohini_code)
        if not embed_token:
            self.log_error('TPA Login Credentials', self.user_name, "Embed Token is NULL")
            return None
        content = self.get_content_from_site(embed_token, ma_id)
        if not content:
            return None
        return content