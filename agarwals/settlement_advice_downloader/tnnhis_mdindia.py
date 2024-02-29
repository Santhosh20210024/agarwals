import requests
import json
from agarwals.settlement_advice_downloader.downloader import Downloader

class Tnnhis_Mdindia(Downloader):
    tpa='MD India Healthcare TPA Service Ltd'
    def __init__(self,branch_code):
        self.branch_code=branch_code
        Downloader.__init__(self)
        
    def download(self):
        try:
            login_url = "https://tnnhis.mdindia.com/"
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
            'Cookie': 'ASP.NET_SessionId=lash3c4fetztz00ckgiucdci'
            }
            login_response = requests.get(login_url, headers=login_headers, params=login_param)
            download_url = "https://tnnhis.mdindia.com/InfoInDraft/SearchPreauthListToGrid"
            download_payload = "pq_datatype=JSON&DsearchCriteria=select&TsearchCriteria=&FromDate=&ToDate=&SearchType=Inpatient"
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

            download_response = requests.post(download_url, headers=download_headers, data=download_payload)
            file_name=f"{self.tpa}_{self.branch_code}.xlsx"
            content_json=json.loads(download_response.content.decode('utf-8'))
            if content_json:
                self.write_Json(file_name=file_name,content=content_json["data"])
            print("downloaded",file_name)
        except Exception as e:
            self.log_error('TPA Login Credentials',self.user_name,e)