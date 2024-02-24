import frappe
import requests
import json
import frappe
import shutil
import os
from agarwals.utils.file_util import construct_file_url

class Downloader():
    tpa=''
    hospital_branch=''
    def __init__(self):
        print("tpa",self.hospital_branch)
        credential_doc = frappe.db.get_list("TPA Login Credentials", filters={"hospital_branch":['=',self.hospital_branch],"tpa":['=',self.tpa]},fields="*")
        if credential_doc:
            self.user_name = credential_doc[0].user_name
            self.password = credential_doc[0].password
        else:
            self.log_error('TPA Login Credentials',self.user_name,"No Credenntial for the given input")
        self.PROJECT_FOLDER = "DrAgarwals"
        self.HOME_PATH = "Home/DrAgarwals"
        self.SHELL_PATH = "private/files"
        self.SUB_DIR = ["Extract", "Transform", "Load", "Bin"]
        self.SITE_PATH=frappe.get_single("Control Panel").site_path
        
    def delete_backend_files(self,file_path=None):
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def write_file(self,file_name=None,content=None):
        if file_name and content:
            with open(file_name, "wb") as file:
                file.write(content)
            shutil.move(file_name,  construct_file_url(self.SITE_PATH, self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0]))
            file=frappe.new_doc("File")
            file.folder = construct_file_url(self.HOME_PATH, self.SUB_DIR[0])
            file.is_private=1
            file.file_url= "/" + construct_file_url(self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0], file_name)
            file.save(ignore_permissions=True)
            self.delete_backend_files(file_path=construct_file_url(self.SITE_PATH, self.SHELL_PATH, self.PROJECT_FOLDER, self.SUB_DIR[0],file_name))
            file_url="/"+construct_file_url(self.SHELL_PATH, file_name)
            frappe.db.commit()
            self.create_fileupload(file_url)
    
    def create_fileupload(self,file_url):
        file_upload_doc=frappe.new_doc("File upload")
        file_upload_doc.document_type="Settlement Advice"
        file_upload_doc.payer_type=self.tpa
        file_upload_doc.upload=file_url
        file_upload_doc.save(ignore_permissions=True)
        frappe.db.commit()

    def log_error(self,doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()
        
class Mediassist(Downloader):
    tpa='Mediassist India Tpa P Ltd'
    def __init__(self,hospital_branch):
        self.hospital_branch=hospital_branch
        Downloader.__init__(self)
        
    def download(self):
        try:
            login_url="https://api-crm-inpatient-v2.ihx.in/Provider/Login"
            login_header={"authority":"api-crm-inpatient-v2.ihx.in","origin":"https://provider.ihx.in","content-type":"application/json","accept":"application/json, text/plain, */*"}
            login_data={"userName":self.user_name,"password":self.password}
            login_response = requests.post(login_url,headers=login_header,json=login_data)
            embed_url="https://profile.ihx.in/Dashboard/PowerBi"
            embed_header={"authority":"profile.ihx.in","accesstoken":login_response.json()["accessToken"],"origin":"https://provider.ihx.in","content-type":"application/json","accept":"application/json, text/plain, */*"}
            embed_data={"applicationId":9233,"dashboardType":"IHX_Finance_Provider_New","profileId":login_response.json()["userDetail"]["profileId"],"providerId":login_response.json()["providerDetail"]["providerId"],"providerName":login_response.json()["providerDetail"]["providerName"],"rohiniCode":login_response.json()["providerDetail"]["providerRohiniCode"]}
            embed_response = requests.post(embed_url,headers=embed_header,json=embed_data)
            download_url="https://wabi-india-central-a-primary-redirect.analysis.windows.net/export/xlsx"
            download_header={"authority":"wabi-india-central-a-primary-redirect.analysis.windows.net","authorization":f"EmbedToken {embed_response.json()['embedToken']['token']}","origin":"https://app.powerbi.com","content-type":"application/json;charset=UTF-8","accept":"application/json, text/plain, */*",}
            download_data={"exportDataType": 2,"executeSemanticQueryRequest": {"version": "1.0.0","queries": [{"Query": {"Commands": [{"SemanticQueryDataShapeCommand": {"Query": {"Version": 2,"From": [{"Name": "h","Entity": "Hospital Claim Data","Type": 0}],
                            "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Hospital Name"},"Name": "Hospital Claim Data.Hospital Name"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "RohiniId"},"Name": "Hospital Claim Data.RohiniId"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "LocationUpdated"},"Name": "Hospital Claim Data.LocationUpdated"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Patient Name"},"Name": "Hospital Claim Data.Patient Name"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Patient Contact"},"Name": "Hospital Claim Data.Patient Contact"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "In Patient Number"},"Name": "Hospital Claim Data.In Patient Number"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Member/Customer ID"},"Name": "Hospital Claim Data.Member/Customer ID"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Date of Admission"},"Name": "Hospital Claim Data.Date of Admission"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Date of Discharge"},"Name": "Hospital Claim Data.Date of Discharge"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Insurance Company Name"},"Name": "Hospital Claim Data.Insurance Company Name"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "TPA Name"},"Name": "Hospital Claim Data.TPA Name"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Policy Number"},"Name": "Hospital Claim Data.Policy Number"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Claim Number"},"Name": "Hospital Claim Data.Claim Number"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Claim Creation Date"},"Name": "Hospital Claim Data.Claim Creation Date"},
                                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Claimed Amount"}},"Function": 0},"Name": "Sum(Hospital Claim Data.Claimed Amount)"},{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Approved Amount"}},"Function": 0},"Name": "Sum(Hospital Claim Data.Approved Amount)"},
                                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Copay"}},"Function": 0},"Name": "Sum(Hospital Claim Data.Copay)"},{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Shortfall Amount"}},"Function": 0},"Name": "Sum(Hospital Claim Data.Shortfall Amount)"},
                                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Hospital Discount"}},"Function": 0},"Name": "Sum(Hospital Claim Data.Hospital Discount)"},{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Patient Paid Amount"}},"Function": 0},"Name": "Sum(Hospital Claim Data.Patient Paid Amount)"},
                                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Settled Amount"}},"Function": 0},"Name": "Sum(Hospital Claim Data.Settled Amount)"},{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "TDS Amount"}},"Function": 0},"Name": "Sum(Hospital Claim Data.TDS Amount)"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Cheque/ NEFT/ UTR No."},"Name": "Hospital Claim Data.Cheque/ NEFT/ UTR No."},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Cheque/ NEFT/ UTR Date"},"Name": "Hospital Claim Data.Cheque/ NEFT/ UTR Date"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Claim Status"},"Name": "Hospital Claim Data.Claim Status"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Treatment "},"Name": "Hospital Claim Data.Treatment "},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Diagnosis"},"Name": "Hospital Claim Data.Diagnosis"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Policy Type (Base/Top-up)"},"Name": "Hospital Claim Data.Policy Type (Base/Top-up)"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Policy Holder Name"},"Name": "Hospital Claim Data.Policy Holder Name"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Employee Code"},"Name": "Hospital Claim Data.Employee Code"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Claim Remarks"},"Name": "Hospital Claim Data.Claim Remarks"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Courier provider"},"Name": "Hospital Claim Data.Courier provider"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Courier Reference ID"},"Name": "Hospital Claim Data.Courier Reference ID"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Document Submission Date (on IHX)"},"Name": "Hospital Claim Data.Document Submission Date (on IHX)"},
                                    {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Payment Update Date"},"Name": "Hospital Claim Data.Payment Update Date"},{"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "InitialPayerClaimNo"},"Name": "Hospital Claim Data.InitialPayerClaimNo","NativeReferenceName": "Initial Claim Number"}],"Where": [{"Condition": {"In": {"Expressions": [
                                            {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "MaMasterId"}}],"Values": [[{"Literal": {"Value": f"{login_response.json()['userDetail']['properties']['MAID']}L"}
                                                                                                                                              }]]}}}],"OrderBy": [{"Direction": 2,"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "h"}},"Property": "Policy Number"}}}]},
                                            "Binding": {"Primary": {"Groupings": [{"Projections": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35]}]},"DataReduction": {"Primary": {"Top": {"Count": 1000000}},"Secondary": {"Top": {"Count": 100}}},"Version": 1}
                                        }},
                            {"ExportDataCommand": {"Columns": [{"QueryName": "Hospital Claim Data.Hospital Name","Name": "Hospital Name"},{"QueryName": "Hospital Claim Data.RohiniId","Name": "RohiniId"},{"QueryName": "Hospital Claim Data.LocationUpdated","Name": "Location"},{"QueryName": "Hospital Claim Data.Patient Name","Name": "Patient Name"},
                                        {"QueryName": "Hospital Claim Data.Patient Contact","Name": "Patient Contact"},{"QueryName": "Hospital Claim Data.In Patient Number","Name": "In Patient Number"},{"QueryName": "Hospital Claim Data.Member/Customer ID","Name": "Member/Customer ID"},{"QueryName": "Hospital Claim Data.Date of Admission","Name": "Date of Admission"},
                                        {"QueryName": "Hospital Claim Data.Date of Discharge","Name": "Date of Discharge"},{"QueryName": "Hospital Claim Data.Insurance Company Name","Name": "Insurance Company Name"},{"QueryName": "Hospital Claim Data.TPA Name","Name": "TPA Name"},{"QueryName": "Hospital Claim Data.Policy Number","Name": "Policy Number"},
                                        {"QueryName": "Hospital Claim Data.Claim Number","Name": "Claim Number"},{"QueryName": "Hospital Claim Data.Claim Creation Date","Name": "Claim Creation Date"},{"QueryName": "Sum(Hospital Claim Data.Claimed Amount)","Name": "Claimed Amount"},{"QueryName": "Sum(Hospital Claim Data.Approved Amount)","Name": "Approved Amount"},
                                        {"QueryName": "Sum(Hospital Claim Data.Copay)","Name": "Copay"},{"QueryName": "Sum(Hospital Claim Data.Shortfall Amount)","Name": "Shortfall Amount"},{"QueryName": "Sum(Hospital Claim Data.Hospital Discount)","Name": "Hospital Discount"},{"QueryName": "Sum(Hospital Claim Data.Patient Paid Amount)","Name": "Patient Paid Amount"},
                                        {"QueryName": "Sum(Hospital Claim Data.Settled Amount)","Name": "Settled Amount"},{"QueryName": "Sum(Hospital Claim Data.TDS Amount)","Name": "TDS Amount"},{"QueryName": "Hospital Claim Data.Cheque/ NEFT/ UTR No.","Name": "Cheque/ NEFT/ UTR No."},{"QueryName": "Hospital Claim Data.Cheque/ NEFT/ UTR Date","Name": "Cheque/ NEFT/ UTR Date"},
                                        {"QueryName": "Hospital Claim Data.Claim Status","Name": "Claim Status"},{"QueryName": "Hospital Claim Data.Treatment ","Name": "Treatment "},{"QueryName": "Hospital Claim Data.Diagnosis","Name": "Diagnosis"},{"QueryName": "Hospital Claim Data.Policy Type (Base/Top-up)","Name": "Policy Type (Base/Top-up)"},
                                        {"QueryName": "Hospital Claim Data.Policy Holder Name","Name": "Policy Holder Name"},{"QueryName": "Hospital Claim Data.Employee Code","Name": "Employee Code"},{"QueryName": "Hospital Claim Data.Claim Remarks","Name": "Claim Remarks"},{"QueryName": "Hospital Claim Data.Courier provider","Name": "Courier provider"},
                                        {"QueryName": "Hospital Claim Data.Courier Reference ID","Name": "Courier Reference ID"},{"QueryName": "Hospital Claim Data.Document Submission Date (on IHX)","Name": "Document Submission Date (on IHX)"},{"QueryName": "Hospital Claim Data.Payment Update Date","Name": "Payment Update Date"},{"QueryName": "Hospital Claim Data.InitialPayerClaimNo","Name": "Initial Claim Number"}],
                                        "Ordering": [0,1,2,3,4,5,6,7,8,10,9,11,12,35,13,14,15,16,17,18,19,20,21,22,23,24,33,34,25,26,27,28,29,30,31,32],f"FiltersDescription": f"Applied filters:\nMaMasterId is {login_response.json()['userDetail']['properties']['MAID']}"}}]}}],"cancelQueries": [],"modelId": 1263249,"userPreferredLocale": "en-US"},"artifactId": 1306251}
            download_response = requests.post(download_url,headers=download_header,json=download_data)
            file_name=f"{self.tpa}_{self.hospital_branch}_{str(frappe.utils.now()).split('.')[0].replace(' ', '-')}.xlsx"
            self.write_file(file_name=file_name,content=download_response.content)
            print("downloaded",file_name)
        except Exception as e:
            self.log_error('TPA Login Credentials',self.user_name,e)