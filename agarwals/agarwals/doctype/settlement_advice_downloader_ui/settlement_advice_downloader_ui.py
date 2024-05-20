# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SettlementAdviceDownloaderUI(Document):
    def isNew(self):
    	record = frappe.db.sql(f"SELECT name FROM `tabSettlement Advice Downloader UI` WHERE name = '{self.name}' ")
    	return False if record else True


    def get_logins(self):
        if self.isNew() == False:
            return

        logins = frappe.get_all('TPA Login Credentials', {'tpa': self.tpa_name, 'is_captcha': 1,'is_enable':1},
                                'name')
        if logins:
            for i in range(0, len(logins)):
                self.append('logins', {
                    'tpa_login_credentials': logins[i].name,
                    'status': 'Open'
                })
            self.status = 'InProgress'
        else:
            frappe.throw(" There is No Login Credential ")
        return

    def get_value(self):
        print("enter captcha from original doc : ", self.captcha)
        return self.captcha if self.captcha else None

    def before_save(self):
        self.get_logins()




@frappe.whitelist()
def update_logins(doc_name):
    if (frappe.db.sql(f"SELECT status FROM `tabSettlement Advice Downloader UI Logins` WHERE parent = '{doc_name}' AND status = 'Retry'")):
        doc = frappe.get_doc("Settlement Advice Downloader UI", doc_name)
        for i in range(0,len(doc.logins)):
            if doc.logins[i].status == 'Retry':
                doc.logins[i].status = 'Open'
        doc.status = "InProgress"
        doc.retry_invalid_captcha = 0
        doc.save()
    else:
        frappe.throw("No Invalid Captcha Logins")



    




