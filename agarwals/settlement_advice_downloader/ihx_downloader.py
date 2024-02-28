from agarwals.settlement_advice_downloader.downloader import Downloader
import frappe
from agarwals.utils.path_data import PROJECT_FOLDER,HOME_PATH,SHELL_PATH,SUB_DIR
import requests

class IHXDownloader(Downloader):
    def __init__(self,tpa,branch_name):
        super().__init__()
        self.tpa = tpa
        self.branch_name = branch_name

    def get_access_token_and_provider_details(self, username, password):
        login_url = "https://api-crm-inpatient-v2.ihx.in/Provider/Login"
        login_header = {"authority": "api-crm-inpatient-v2.ihx.in", "origin": "https://provider.ihx.in",
                        "content-type": "application/json", "accept": "application/json, text/plain, */*"}
        login_data = {"userName": username, "password": password}
        login_response = requests.post(login_url, headers=login_header, json=login_data)
        response_json = login_response.json()
        if response_json["access_token"] and login_response.status_code == 200:
            return response_json["access_token"],response_json['userDetial']['profileId'], response_json['providerDetail']['providerId'], response_json['providerDetail']['providerName'], response_json['providerDetail']['providerRohiniCode'], response_json['userDetail']['properties']['MAID']
        return None, None, None, None, None, None

    def get_embed_token(self,access_token,profile_id,provider_id,provider_name, rohini_code):
        embed_url = "https://profile.ihx.in/Dashboard/PowerBi"
        embed_header = {"authority": "profile.ihx.in", "accesstoken": access_token,
                        "origin": "https://provider.ihx.in", "content-type": "application/json",
                        "accept": "application/json, text/plain, */*"}
        embed_data = {"applicationId": 9233, "dashboardType": "IHX_Finance_Provider_New",
                      "profileId": profile_id,
                      "providerId": provider_id,
                      "providerName": provider_name,
                      "rohiniCode": rohini_code}
        embed_response = requests.post(embed_url, headers=embed_header, json=embed_data)
        response_json = embed_response.json()
        if response_json['embedToken']['token'] and embed_response.status_code == 200:
            return response_json['embedToken']['token']
        return None

    def download_excel(self,embed_token, ma_id):
        download_url = "https://wabi-india-central-a-primary-redirect.analysis.windows.net/export/xlsx"
        download_header = {"authority": "wabi-india-central-a-primary-redirect.analysis.windows.net",
                           "authorization": f"EmbedToken {embed_token}",
                           "origin": "https://app.powerbi.com", "content-type": "application/json;charset=UTF-8",
                           "accept": "application/json, text/plain, */*", }
        download_data = {"exportDataType": 2, "executeSemanticQueryRequest": {"version": "1.0.0", "queries": [{
                                                                                                                  "Query": {
                                                                                                                      "Commands": [
                                                                                                                          {
                                                                                                                              "SemanticQueryDataShapeCommand": {
                                                                                                                                  "Query": {
                                                                                                                                      "Version": 2,
                                                                                                                                      "From": [
                                                                                                                                          {
                                                                                                                                              "Name": "h",
                                                                                                                                              "Entity": "Hospital Claim Data",
                                                                                                                                              "Type": 0}],
                                                                                                                                      "Select": [
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Hospital Name"},
                                                                                                                                              "Name": "Hospital Claim Data.Hospital Name"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "RohiniId"},
                                                                                                                                              "Name": "Hospital Claim Data.RohiniId"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "LocationUpdated"},
                                                                                                                                              "Name": "Hospital Claim Data.LocationUpdated"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Patient Name"},
                                                                                                                                              "Name": "Hospital Claim Data.Patient Name"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Patient Contact"},
                                                                                                                                              "Name": "Hospital Claim Data.Patient Contact"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "In Patient Number"},
                                                                                                                                              "Name": "Hospital Claim Data.In Patient Number"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Member/Customer ID"},
                                                                                                                                              "Name": "Hospital Claim Data.Member/Customer ID"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Date of Admission"},
                                                                                                                                              "Name": "Hospital Claim Data.Date of Admission"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Date of Discharge"},
                                                                                                                                              "Name": "Hospital Claim Data.Date of Discharge"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Insurance Company Name"},
                                                                                                                                              "Name": "Hospital Claim Data.Insurance Company Name"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "TPA Name"},
                                                                                                                                              "Name": "Hospital Claim Data.TPA Name"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Policy Number"},
                                                                                                                                              "Name": "Hospital Claim Data.Policy Number"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Claim Number"},
                                                                                                                                              "Name": "Hospital Claim Data.Claim Number"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Claim Creation Date"},
                                                                                                                                              "Name": "Hospital Claim Data.Claim Creation Date"},
                                                                                                                                          {
                                                                                                                                              "Aggregation": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "Column": {
                                                                                                                                                          "Expression": {
                                                                                                                                                              "SourceRef": {
                                                                                                                                                                  "Source": "h"}},
                                                                                                                                                          "Property": "Claimed Amount"}},
                                                                                                                                                  "Function": 0},
                                                                                                                                              "Name": "Sum(Hospital Claim Data.Claimed Amount)"},
                                                                                                                                          {
                                                                                                                                              "Aggregation": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "Column": {
                                                                                                                                                          "Expression": {
                                                                                                                                                              "SourceRef": {
                                                                                                                                                                  "Source": "h"}},
                                                                                                                                                          "Property": "Approved Amount"}},
                                                                                                                                                  "Function": 0},
                                                                                                                                              "Name": "Sum(Hospital Claim Data.Approved Amount)"},
                                                                                                                                          {
                                                                                                                                              "Aggregation": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "Column": {
                                                                                                                                                          "Expression": {
                                                                                                                                                              "SourceRef": {
                                                                                                                                                                  "Source": "h"}},
                                                                                                                                                          "Property": "Copay"}},
                                                                                                                                                  "Function": 0},
                                                                                                                                              "Name": "Sum(Hospital Claim Data.Copay)"},
                                                                                                                                          {
                                                                                                                                              "Aggregation": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "Column": {
                                                                                                                                                          "Expression": {
                                                                                                                                                              "SourceRef": {
                                                                                                                                                                  "Source": "h"}},
                                                                                                                                                          "Property": "Shortfall Amount"}},
                                                                                                                                                  "Function": 0},
                                                                                                                                              "Name": "Sum(Hospital Claim Data.Shortfall Amount)"},
                                                                                                                                          {
                                                                                                                                              "Aggregation": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "Column": {
                                                                                                                                                          "Expression": {
                                                                                                                                                              "SourceRef": {
                                                                                                                                                                  "Source": "h"}},
                                                                                                                                                          "Property": "Hospital Discount"}},
                                                                                                                                                  "Function": 0},
                                                                                                                                              "Name": "Sum(Hospital Claim Data.Hospital Discount)"},
                                                                                                                                          {
                                                                                                                                              "Aggregation": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "Column": {
                                                                                                                                                          "Expression": {
                                                                                                                                                              "SourceRef": {
                                                                                                                                                                  "Source": "h"}},
                                                                                                                                                          "Property": "Patient Paid Amount"}},
                                                                                                                                                  "Function": 0},
                                                                                                                                              "Name": "Sum(Hospital Claim Data.Patient Paid Amount)"},
                                                                                                                                          {
                                                                                                                                              "Aggregation": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "Column": {
                                                                                                                                                          "Expression": {
                                                                                                                                                              "SourceRef": {
                                                                                                                                                                  "Source": "h"}},
                                                                                                                                                          "Property": "Settled Amount"}},
                                                                                                                                                  "Function": 0},
                                                                                                                                              "Name": "Sum(Hospital Claim Data.Settled Amount)"},
                                                                                                                                          {
                                                                                                                                              "Aggregation": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "Column": {
                                                                                                                                                          "Expression": {
                                                                                                                                                              "SourceRef": {
                                                                                                                                                                  "Source": "h"}},
                                                                                                                                                          "Property": "TDS Amount"}},
                                                                                                                                                  "Function": 0},
                                                                                                                                              "Name": "Sum(Hospital Claim Data.TDS Amount)"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Cheque/ NEFT/ UTR No."},
                                                                                                                                              "Name": "Hospital Claim Data.Cheque/ NEFT/ UTR No."},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Cheque/ NEFT/ UTR Date"},
                                                                                                                                              "Name": "Hospital Claim Data.Cheque/ NEFT/ UTR Date"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Claim Status"},
                                                                                                                                              "Name": "Hospital Claim Data.Claim Status"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Treatment "},
                                                                                                                                              "Name": "Hospital Claim Data.Treatment "},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Diagnosis"},
                                                                                                                                              "Name": "Hospital Claim Data.Diagnosis"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Policy Type (Base/Top-up)"},
                                                                                                                                              "Name": "Hospital Claim Data.Policy Type (Base/Top-up)"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Policy Holder Name"},
                                                                                                                                              "Name": "Hospital Claim Data.Policy Holder Name"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Employee Code"},
                                                                                                                                              "Name": "Hospital Claim Data.Employee Code"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Claim Remarks"},
                                                                                                                                              "Name": "Hospital Claim Data.Claim Remarks"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Courier provider"},
                                                                                                                                              "Name": "Hospital Claim Data.Courier provider"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Courier Reference ID"},
                                                                                                                                              "Name": "Hospital Claim Data.Courier Reference ID"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Document Submission Date (on IHX)"},
                                                                                                                                              "Name": "Hospital Claim Data.Document Submission Date (on IHX)"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "Payment Update Date"},
                                                                                                                                              "Name": "Hospital Claim Data.Payment Update Date"},
                                                                                                                                          {
                                                                                                                                              "Column": {
                                                                                                                                                  "Expression": {
                                                                                                                                                      "SourceRef": {
                                                                                                                                                          "Source": "h"}},
                                                                                                                                                  "Property": "InitialPayerClaimNo"},
                                                                                                                                              "Name": "Hospital Claim Data.InitialPayerClaimNo",
                                                                                                                                              "NativeReferenceName": "Initial Claim Number"}],
                                                                                                                                      "Where": [
                                                                                                                                          {
                                                                                                                                              "Condition": {
                                                                                                                                                  "In": {
                                                                                                                                                      "Expressions": [
                                                                                                                                                          {
                                                                                                                                                              "Column": {
                                                                                                                                                                  "Expression": {
                                                                                                                                                                      "SourceRef": {
                                                                                                                                                                          "Source": "h"}},
                                                                                                                                                                  "Property": "MaMasterId"}}],
                                                                                                                                                      "Values": [
                                                                                                                                                          [
                                                                                                                                                              {
                                                                                                                                                                  "Literal": {
                                                                                                                                                                      "Value": f"{ma_id}L"}
                                                                                                                                                                  }]]}}}],
                                                                                                                                      "OrderBy": [
                                                                                                                                          {
                                                                                                                                              "Direction": 2,
                                                                                                                                              "Expression": {
                                                                                                                                                  "Column": {
                                                                                                                                                      "Expression": {
                                                                                                                                                          "SourceRef": {
                                                                                                                                                              "Source": "h"}},
                                                                                                                                                      "Property": "Policy Number"}}}]},
                                                                                                                                  "Binding": {
                                                                                                                                      "Primary": {
                                                                                                                                          "Groupings": [
                                                                                                                                              {
                                                                                                                                                  "Projections": [
                                                                                                                                                      0,
                                                                                                                                                      1,
                                                                                                                                                      2,
                                                                                                                                                      3,
                                                                                                                                                      4,
                                                                                                                                                      5,
                                                                                                                                                      6,
                                                                                                                                                      7,
                                                                                                                                                      8,
                                                                                                                                                      9,
                                                                                                                                                      10,
                                                                                                                                                      11,
                                                                                                                                                      12,
                                                                                                                                                      13,
                                                                                                                                                      14,
                                                                                                                                                      15,
                                                                                                                                                      16,
                                                                                                                                                      17,
                                                                                                                                                      18,
                                                                                                                                                      19,
                                                                                                                                                      20,
                                                                                                                                                      21,
                                                                                                                                                      22,
                                                                                                                                                      23,
                                                                                                                                                      24,
                                                                                                                                                      25,
                                                                                                                                                      26,
                                                                                                                                                      27,
                                                                                                                                                      28,
                                                                                                                                                      29,
                                                                                                                                                      30,
                                                                                                                                                      31,
                                                                                                                                                      32,
                                                                                                                                                      33,
                                                                                                                                                      34,
                                                                                                                                                      35]}]},
                                                                                                                                      "DataReduction": {
                                                                                                                                          "Primary": {
                                                                                                                                              "Top": {
                                                                                                                                                  "Count": 1000000}},
                                                                                                                                          "Secondary": {
                                                                                                                                              "Top": {
                                                                                                                                                  "Count": 100}}},
                                                                                                                                      "Version": 1}
                                                                                                                                  }},
                                                                                                                          {
                                                                                                                              "ExportDataCommand": {
                                                                                                                                  "Columns": [
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Hospital Name",
                                                                                                                                          "Name": "Hospital Name"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.RohiniId",
                                                                                                                                          "Name": "RohiniId"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.LocationUpdated",
                                                                                                                                          "Name": "Location"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Patient Name",
                                                                                                                                          "Name": "Patient Name"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Patient Contact",
                                                                                                                                          "Name": "Patient Contact"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.In Patient Number",
                                                                                                                                          "Name": "In Patient Number"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Member/Customer ID",
                                                                                                                                          "Name": "Member/Customer ID"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Date of Admission",
                                                                                                                                          "Name": "Date of Admission"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Date of Discharge",
                                                                                                                                          "Name": "Date of Discharge"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Insurance Company Name",
                                                                                                                                          "Name": "Insurance Company Name"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.TPA Name",
                                                                                                                                          "Name": "TPA Name"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Policy Number",
                                                                                                                                          "Name": "Policy Number"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Claim Number",
                                                                                                                                          "Name": "Claim Number"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Claim Creation Date",
                                                                                                                                          "Name": "Claim Creation Date"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Sum(Hospital Claim Data.Claimed Amount)",
                                                                                                                                          "Name": "Claimed Amount"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Sum(Hospital Claim Data.Approved Amount)",
                                                                                                                                          "Name": "Approved Amount"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Sum(Hospital Claim Data.Copay)",
                                                                                                                                          "Name": "Copay"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Sum(Hospital Claim Data.Shortfall Amount)",
                                                                                                                                          "Name": "Shortfall Amount"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Sum(Hospital Claim Data.Hospital Discount)",
                                                                                                                                          "Name": "Hospital Discount"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Sum(Hospital Claim Data.Patient Paid Amount)",
                                                                                                                                          "Name": "Patient Paid Amount"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Sum(Hospital Claim Data.Settled Amount)",
                                                                                                                                          "Name": "Settled Amount"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Sum(Hospital Claim Data.TDS Amount)",
                                                                                                                                          "Name": "TDS Amount"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Cheque/ NEFT/ UTR No.",
                                                                                                                                          "Name": "Cheque/ NEFT/ UTR No."},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Cheque/ NEFT/ UTR Date",
                                                                                                                                          "Name": "Cheque/ NEFT/ UTR Date"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Claim Status",
                                                                                                                                          "Name": "Claim Status"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Treatment ",
                                                                                                                                          "Name": "Treatment "},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Diagnosis",
                                                                                                                                          "Name": "Diagnosis"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Policy Type (Base/Top-up)",
                                                                                                                                          "Name": "Policy Type (Base/Top-up)"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Policy Holder Name",
                                                                                                                                          "Name": "Policy Holder Name"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Employee Code",
                                                                                                                                          "Name": "Employee Code"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Claim Remarks",
                                                                                                                                          "Name": "Claim Remarks"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Courier provider",
                                                                                                                                          "Name": "Courier provider"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Courier Reference ID",
                                                                                                                                          "Name": "Courier Reference ID"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Document Submission Date (on IHX)",
                                                                                                                                          "Name": "Document Submission Date (on IHX)"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.Payment Update Date",
                                                                                                                                          "Name": "Payment Update Date"},
                                                                                                                                      {
                                                                                                                                          "QueryName": "Hospital Claim Data.InitialPayerClaimNo",
                                                                                                                                          "Name": "Initial Claim Number"}],
                                                                                                                                  "Ordering": [
                                                                                                                                      0,
                                                                                                                                      1,
                                                                                                                                      2,
                                                                                                                                      3,
                                                                                                                                      4,
                                                                                                                                      5,
                                                                                                                                      6,
                                                                                                                                      7,
                                                                                                                                      8,
                                                                                                                                      10,
                                                                                                                                      9,
                                                                                                                                      11,
                                                                                                                                      12,
                                                                                                                                      35,
                                                                                                                                      13,
                                                                                                                                      14,
                                                                                                                                      15,
                                                                                                                                      16,
                                                                                                                                      17,
                                                                                                                                      18,
                                                                                                                                      19,
                                                                                                                                      20,
                                                                                                                                      21,
                                                                                                                                      22,
                                                                                                                                      23,
                                                                                                                                      24,
                                                                                                                                      33,
                                                                                                                                      34,
                                                                                                                                      25,
                                                                                                                                      26,
                                                                                                                                      27,
                                                                                                                                      28,
                                                                                                                                      29,
                                                                                                                                      30,
                                                                                                                                      31,
                                                                                                                                      32],
                                                                                                                                  f"FiltersDescription": f"Applied filters:\nMaMasterId is {ma_id}"}}]}}],
                                                                              "cancelQueries": [], "modelId": 1263249,
                                                                              "userPreferredLocale": "en-US"},
                         "artifactId": 1306251}
        download_response = requests.post(download_url, headers=download_header, json=download_data)
        if download_response.status_code != 200:
            return None
        return download_response.content

    def write_to_file(self,file_name, content):
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

    def get_content(self, username, password):
        access_token, profile_id, provider_id, provider_name, rohini_code, ma_id = self.get_access_token_and_provider_details(username,password)
        if not access_token:
            self.log_error('TPA Login Credentials', self.user_name, "Access Token is NULL")
            return None
        embed_token = self.get_embed_token(access_token, profile_id, provider_id, provider_name, rohini_code)
        if not embed_token:
            self.log_error('TPA Login Credentials', self.user_name, "Embed Token is NULL")
            return None
        content = self.get_response_content(embed_token, ma_id)
        if not content:
            return None
        return content


