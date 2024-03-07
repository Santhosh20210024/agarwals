import requests
from agarwals.settlement_advice_downloader.downloader import Downloader

class TipsVidalHealthTpa(Downloader):
    def __init__(self,tpa_name,branch_code, last_executed_time):
        self.tpa=tpa_name
        self.branch_code=branch_code
        self.last_executed_time=last_executed_time
        Downloader.__init__(self)
        
    def get_content_from_site(self):
        session=requests.Session()
        login_url, login_header, login_body, login_params, login_cookies=self.get_meta_data("TipsVidalHealthTpa","login",{"body":[{"{user_name}":self.user_name},{"{password}":self.password}]})
        login_response = session.post(login_url, headers=login_header, data=login_body,cookies=login_cookies)
        cookie=login_response.cookies["JSESSIONID"]
        download_url, download_header, download_body, download_params, download_cookies=self.get_meta_data("TipsVidalHealthTpa","download",{"header":[{"{cookie}":login_response.cookies["JSESSIONID"]}]})
        download_response = session.post(download_url, headers=download_header, data=download_body)
        if download_response.status_code != 200:
            return None
        return download_response.content
    
    def get_file_details(self):
        file_name = f"{self.tpa.replace(' ','').lower()}_{self.user_name}_{self.branch_code}.xls"
        self.is_binary=True
        return file_name
    
    def get_content(self):
        content = self.get_content_from_site()
        if not content:
            return None
        return content