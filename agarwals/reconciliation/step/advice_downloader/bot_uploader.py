import frappe
import requests
import shutil
import os
from tfs.api_utils import login, create_document, create_file
from agarwals.utils.error_handler import log_error
from tfs.orchestration import ChunkOrchestrator, chunk
from agarwals.utils.str_to_dict import cast_to_dic


class SABotUploader:
    def __init__(self):
        self.set_configuration_values()

    def raise_exception(self, exception):
        raise Exception(exception)

    def set_configuration_values(self) -> None:
        """
        Usage:
             Retrieve and set configuration values from the Control Panel.
        Raises:
             Raise exceptions if any required configuration values are missing.
        """
        control_panel = frappe.get_single("Control Panel")
        if control_panel:
            self.user_id = control_panel.user_id or self.raise_exception(
                "User ID cannot be empty; the bot requires it to upload settlement advice files.")
            self.password = control_panel.password or self.raise_exception(
                "Password cannot be empty; the bot requires it to upload settlement advice files.")
            self.url = control_panel.url or self.raise_exception(
                "Destination URL cannot be empty; the bot requires it to upload settlement advice files.")
            site_path = control_panel.site_path or self.raise_exception(
                "Site path cannot be empty; the bot requires it to upload settlement advice files.")
            project_path = control_panel.project_folder or self.raise_exception(
                "Project path cannot be empty; the bot requires it to upload settlement advice files.")
            shell_path = "private/files"
            self.sa_download_path = os.path.join(site_path, shell_path, project_path, "Settlement Advice")
            self.zip_folder_name = f"SA_Zip_{frappe.utils.now_datetime()}"
            self.zip_folder_path = os.path.join(self.sa_download_path, self.zip_folder_name)
            self.folder_names = set(
                frappe.db.sql("SELECT tpa FROM `tabTPA Login Credentials` WHERE is_enable = 1", pluck="tpa"))
            self.send_mail = control_panel.send_mail
            self.mail_group = control_panel.email_group or None
            self.delete_folders_with_zip = control_panel.delete_zip
            self.delete_folders_without_zip = control_panel.delete_folder
            self.file_upload_failed = False


    def convert_folder_to_zip(self) -> None:
        os.mkdir(self.zip_folder_path)
        for folder_name in self.folder_names:
            path = os.path.join(self.sa_download_path, folder_name)
            if not os.path.exists(path):
                log_error(error=f"{path} - Path does not exist While converting folder to zip",
                          doc_name="SA Bot Uploader")
            elif len(os.listdir(path)) < 1:
                log_error(error=f"{folder_name} Folder found empty - While converting folder to zip",
                          doc_name="SA Bot Uploader")
            else:
                zip_name = self.zip_folder_path + "/" + f"{folder_name}[{frappe.utils.now_datetime()}]"
                shutil.make_archive(base_name=zip_name, format="zip", root_dir=path)

        if len(os.listdir(self.zip_folder_path)) == 0:
            self.raise_exception(f"File Upload Failed :{self.zip_folder_path} -Zip files not found ")

    def get_login_session(self) -> None:
        """
       Usage:
            Retrieves an authenticated session by logging into the portal.
       Returns:
            object: An authenticated session object if login is successful
        Raises:
            Exception: If the `login` function raises an exception due to authentication failure
                       or any other issue.
        """
        session = login(self.user_id, self.password, self.url)
        return session

    def upload_zip_files(self) -> None:
        """
        Usage:
            Upload zip files from the specified directory to the server.
        Raises:
            Raise exception if no zip files are found or an upload error occurs.
        """
        zip_files = os.listdir(self.zip_folder_path)
        if zip_files:
            for zip_file in zip_files:
                try:
                    content = {
                        'file_format': 'ZIP',
                        'document_type': 'Settlement Advice',
                        'is_bot': '1',
                        "payer_type": zip_file.split("[")[0],
                        "upload": f"/private/files/{zip_file}"
                    }
                    file_path = self.zip_folder_path + "/" + zip_file
                    create_file(session=self.session, url=self.url, file_path=file_path, file_name=zip_file)
                    create_document(doctype='File upload', url=self.url, session=self.session, content=content)
                except Exception as e:
                    self.file_upload_failed = True
                    log_error(error=f"Failed to Upload  {zip_file}  error = {e}", doc_name="SA Bot Uploader")
        else:
            self.raise_exception("No Zip Files Found")

    def generate_report_table(self):
        tpa_names = list(self.folder_names)
        total_files_downloaded = []
        total_logins = []

        for tpa_name in tpa_names:
            path = self.sa_download_path + tpa_name
            total_files_downloaded.append(len(os.listdir(path)))
            total_logins.append(frappe.db.count('TPA Login Credentials', {'is_enable': 1, 'tpa': tpa_name}))

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
        return html_table, sum(total_files_downloaded), sum(total_logins)

    def send_notification(self, message, subject, reciver_list):
        frappe.sendmail(recipients=reciver_list, subject=subject, message=message)

    def generate_notification(self):
        if not self.mail_group:
            self.raise_exception("Mail Group Not Found")

        reciver_list = frappe.db.sql(
            f" SELECT email FROM `tabEmail Group Member` WHERE email_group = '{self.mail_group}' ", pluck='email')
        if not reciver_list:
            self.raise_exception("Group Has No Recivers")

        report_table, total_file_downloaded, total_logins = self.generate_report_table()
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
        frappe.enqueue(self.send_notification, queue='long', message=message, subject=subject,
                       reciver_list=reciver_list)

    def delete_backend_file(self):
        folders = os.listdir(self.sa_download_path)
        for folder in folders:
            path = self.sa_download_path + folder
            if folder not in ['Error', self.zip_folder_name]:
                if os.path.exists(path):
                    if folder.endswith('zip'):
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
                else:
                    log_error("Path Dose not Exits While removing the folder ")
        if self.delete_folders_with_zip == 1 and self.file_upload_failed == False:
            if os.path.exists(self.zip_folder_path):
                shutil.rmtree(self.zip_folder_path)


    @ChunkOrchestrator.update_chunk_status
    def process(self) -> None:
        """
        Usage:
            Execute the entire process of converting folders to zip files, uploading them,
            generating notifications, and deleting backend files based on configuration.
        Returns:
            None
        """
        try:
            self.convert_folder_to_zip()
            self.session = self.get_login_session()
            self.upload_zip_files()
            if self.send_mail == 1:
                self.generate_notification()
            if self.delete_folders_without_zip == 1 or self.delete_folders_with_zip == 1:
                self.delete_backend_file()
            return "Processed"
        except Exception as e:
            log_error(error=e, doc_name="SA Bot Uploader")
            return "Error"


@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        bot_uploader = SABotUploader()
        ChunkOrchestrator().process(bot_uploader.process, step_id=args["step_id"], is_enqueueable=True,
                                    queue=args["queue"],
                                    is_async=True, timeout=3600)
    except Exception as e:
        log_error(error=e,doc_name='SA Bot Uploader')