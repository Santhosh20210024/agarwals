import frappe
import requests

class Downloader():
    def __init__(self):
        credential_doc = frappe.db.get_list("TPA Login Credentials", filters={"branch":['like',self.branch],"tpa":['like',f'{tpa_name}%']})
        self.user_name = credential_doc.user_name
        self.password = credential_doc.password
        self.tpa=''
        self.branch=''
        self.url = credential_doc.url
    
    def set_login_credential(self,tpa_name=None,branch_name=None):
        credential_doc = frappe.db.get_list("TPA Login Credentials", filters={"branch":['=',f'{branch_name}%'],"tpa":['like',f'{tpa_name}%']})
        self.user_name = credential_doc.user_name
        self.password = credential_doc.password
        self.tpa=credential_doc.tpa
        self.branch=credential_doc.branch
        self.url = credential_doc.url
        
class Mediassist(Downloader):
    def __init__(self,branch):
        super().__init__()
        self.tpa='Mediassist India Tpa P Ltd'
        self.branch=branch
    
    def download(self,tpa_name=None,branch_name=None):
        self.set_login_credential(tpa_name=tpa_name,branch_name=branch_name)
        