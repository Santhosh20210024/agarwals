import requests
from agarwals.website_downloader.downloader import Downloader

class TipsVidalHealthTpa(Downloader):
    def __init__(self,tpa_name,branch_code):
        self.tpa=tpa_name
        self.branch_code=branch_code
        Downloader.__init__(self)
        
    def download(self):
        try:
            session=requests.Session()
            login_url = "https://tips.vidalhealthtpa.com/hospitallogin/hospital/login/loginAction.html"
            cookies = {'JSESSIONID': '12345677'}
            login_payload = 'hosUserID=NITAASHAH&hosPassword=Nas%402460'
            login_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://tips.vidalhealthtpa.com',
            'Referer': 'https://tips.vidalhealthtpa.com/hospitallogin/hospital/login/loginAction.html',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
            }
            login_response = session.post(login_url, headers=login_headers, data=login_payload,cookies=cookies)
            download_url = "https://tips.vidalhealthtpa.com/hospitallogin/hospital/reports/consolidatedreports.html?fromdate=28/11/2023&todate=26/02/2024"
            download_payload = 'fromDate=28%2F11%2F2023&toDate=26%2F02%2F2024'
            download_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': f'JSESSIONID={login_response.cookies["JSESSIONID"]}',
            'Origin': 'https://tips.vidalhealthtpa.com',
            'Referer': 'https://tips.vidalhealthtpa.com/hospitallogin/hospital/reports/reports.html',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
            }

            download_response = session.post(download_url, headers=download_headers, data=download_payload)
            file_name=f"{self.tpa}_{self.branch_code}.xls"
            if download_response.content:
                self.write_binary(file_name=file_name,content=download_response.content)
            print("downloaded",file_name)
        except Exception as e:
            self.log_error('TPA Login Credentials',self.user_name,e)

