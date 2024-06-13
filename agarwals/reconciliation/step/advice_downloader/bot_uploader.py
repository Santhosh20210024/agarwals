import frappe
import requests
import shutil
import os
from agarwals.utils.error_handler import log_error

class SABotUploader:
    def __init__(self):
        self.user_id = None
        self.password = None
        self.url = None
        self.sa_download_path = None
        self.zip_folder_name = None
        self.zip_folder_path = None
        self.session = None
        self.folder_names = None
        self.send_mail = None
        self.mail_group = None
        self.delete_zip_folder = None

    def raise_exception(self,exception):
        raise Exception(exception)

    def set_self_variable(self):
        control_panel = frappe.get_single("Control Panel")
        if control_panel:
            self.user_id = control_panel.user_id
            self.password = control_panel.password
            self.url = control_panel.url if control_panel.url.endswith("/") else control_panel.url + "/"
            self.sa_download_path = control_panel.sa_downloader_path if control_panel.sa_downloader_path.endswith("/") else control_panel.sa_downloader_path + "/"
            self.zip_folder_name = f"SA_Zip_{frappe.utils.now_datetime()}"
            self.zip_folder_path = self.sa_download_path+self.zip_folder_name
            self.folder_names = set(frappe.db.sql("SELECT tpa FROM `tabTPA Login Credentials` WHERE is_enable = 1",pluck ="tpa"))
            self.send_mail = control_panel.send_mail if control_panel.send_mail else None
            self.mail_group = control_panel.email_group if control_panel.email_group else None
            self.delete_zip_folder = control_panel.delete_zip = 1 if control_panel.delete_zip else None

    def convert_folder_to_zip(self):
        os.mkdir(self.zip_folder_path)
        for folder_name in self.folder_names:
            path = self.sa_download_path + folder_name
            if not os.path.exists(path):
                log_error(error=f"{path} - Path does not exist While converting folder to zip",doc_name="SA Bot Uploader")
            elif len(os.listdir(path)) < 1:
                log_error(error=f"{folder_name} Folder found empty - While converting folder to zip",doc_name="SA Bot Uploader")
            else:
                zip_name = self.zip_folder_path +"/"+f"{folder_name}[{frappe.utils.now_datetime()}]"
                convert_zip = shutil.make_archive(base_name=zip_name, format="zip", root_dir=path)

        if len(os.listdir(self.zip_folder_path)) == 0:
            self.raise_exception(f"File Upload Failed :{self.zip_folder_path} -Zip files not found ")

    def login(self):
        self.session = requests.Session()
        login_url = self.url + "/api/method/login"
        payload = {
            'usr': self.user_id,
            'pwd': self.password
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = self.session.post(login_url, json=payload, headers=headers)
        if response.status_code != 200:
            self.raise_exception(f"Login Failed : Error = {response.text} , Status Code = {response.status_code}")


    def upload_zip_files(self):
        zip_files = os.listdir(self.zip_folder_path)
        if zip_files:
            for zip_file in zip_files:
                file_upload_url = f'{self.url}api/method/upload_file'
                file_path = self.zip_folder_path+"/"+zip_file
                file_name = zip_file

                with open(file_path, 'rb') as file_obj:
                    files = {
                        'file': (file_name, file_obj)
                    }
                    data = {
                        'is_private': 1,
                        'folder': 'Home/Attachments'
                    }

                    upload_response = self.session.post(file_upload_url, files=files, data=data)
                    if upload_response.status_code == 200:
                        create_file_upload = f'{self.url}api/resource/File upload'
                        payload = {
                            'file_format': 'ZIP',
                            'document_type': 'Settlement Advice',
                            'is_bot': '1',
                            "payer_type": file_name.split("[")[0],
                            "upload": f"/private/files/{file_name}"
                        }
                        response = self.session.post(create_file_upload, json=payload)
                        if response.status_code != 200:
                            self.raise_exception(f"file created but file upload filed ")
                    else:
                        self.raise_exception(f"Upload Failed : Error ")
        else:
            self.raise_exception("No Zip Files Found")

    def generate_report_table(self):
        tpa_names = list(self.folder_names)
        total_files_downloaded = []
        total_logins = []

        for tpa_name in tpa_names:
            path = self.sa_download_path + tpa_name
            total_files_downloaded.append(len(os.listdir(path)))
            total_logins.append(frappe.db.count('TPA Login Credentials',{'is_enable':1,'tpa':tpa_name}))

        html_table = """
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>TPA Name</th>
                <th>Total Files Downloaded</th>
                <th>Total Logins</th>
            </tr>
        """

        for tpa_name, files_downloaded, logins in zip(tpa_names, total_files_downloaded, total_logins):
            html_table += f"""
            <tr>
                <td>{tpa_name}</td>
                <td>{files_downloaded}</td>
                <td>{logins}</td>
            </tr>
            """
        html_table += "</table>"
        return html_table,sum(total_files_downloaded),sum(total_logins)

    def send_notification(self,message,subject,reciver_list):
        frappe.sendmail(recipients=reciver_list,subject=subject,message=message)

    def generate_notification(self):
        if not self.mail_group:
            self.raise_exception("Mail Group Not Found")

        reciver_list = frappe.db.sql(f" SELECT email FROM `tabEmail Group Member` WHERE email_group = '{self.mail_group}' ",pluck= 'email')
        if not reciver_list:
            self.raise_exception("Group Has No Recivers")

        report_table,total_file_downloaded,total_logins = self.generate_report_table()
        subject = "Settlement Advice Downloader Report"
        message = f"""
        Hi All,<br>
        The report of Settlement Advice downloaded today is as follows:
        <br> 
        Total logins = {total_logins} and Total files downloaded = {total_file_downloaded}.
        <br>
        {report_table}
        <br> 
        Thanks,
        <br>
        SA Downloader BOT
        """
        frappe.enqueue(self.send_notification,queue='long',message=message,subject=subject,reciver_list=reciver_list)

    def delete_backend_file(self):
        for folder in self.folder_names:
            path = self.sa_download_path + folder
            if os.path.exists(path):
                shutil.rmtree(path)
            else:
                log_error("Path Dose not Exits While removing the folder ")
        if self.delete_zip_folder == 1:
            if os.path.exists(self.zip_folder_path):
                shutil.rmtree(self.zip_folder_path)

    def process(self):
        try:
            self.set_self_variable()
            self.convert_folder_to_zip()
            self.login()
            self.upload_zip_files()
            if self.send_mail == 1:
                self.generate_notification()
            self.delete_backend_file()
        except Exception as e:
            log_error(error=e,doc_name="SA Bot Uploader")
