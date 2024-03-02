import requests
import json
from agarwals.settlement_advice_downloader.downloader import Downloader

class TnnhisMdIndia(Downloader):
    def __init__(self,tpa_name,branch_code):
        self.tpa=tpa_name
        self.branch_code=branch_code
        Downloader.__init__(self)
        
    def get_content_from_site(self):
        session=requests.Session()
        login_url = "https://tnnhis.mdindia.com/"
        cookies = {'ASP.NET_SessionId': '12345677'}
        login_param = {"ProviderCode":self.user_name,"ProviderPassword":self.password}
        login_headers = {
        'authority': 'tnnhis.mdindia.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://tnnhis.mdindia.com/',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }
        login_response = session.get(login_url, headers=login_headers, params=login_param, cookies=cookies)
        download_url = "https://tnnhis.mdindia.com/InfoInDraft/SearchPreauthListToGrid"
        download_payload = "pq_datatype=JSON&DsearchCriteria=select&TsearchCriteria=&FromDate=&ToDate=&SearchType=Total+Paid+Claims+Count"
        download_headers = {
        'authority': 'tnnhis.mdindia.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'cookie': f"ASP.NET_SessionId={login_response.cookies['ASP.NET_SessionId']}",
        'origin': 'https://tnnhis.mdindia.com',
        'referer': 'https://tnnhis.mdindia.com/InfoInDraft/SearchPreauthList',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-requested-with': 'XMLHttpRequest'
        }
        download_response = session.post(download_url, headers=download_headers, data=download_payload)
        content_json=json.loads(download_response.content.decode('utf-8'))
        if download_response.status_code != 200:
            return None
        return content_json["data"]
        
    def get_file_details(self):
        file_name = f"{self.tpa.replace(' ','').lower()}_{self.user_name}_{self.branch_code}.xlsx"
        self.is_json=True
        return file_name
    
    def get_content(self):
        content = self.get_content_from_site()
        if not content:
            self.log_error('TPA Login Credentials', self.user_name, "No Data")
            return None
        return content