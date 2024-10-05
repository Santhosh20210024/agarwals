# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

class BillEntry(Document):
	def set_none_value(self):
		self.bill = None
		self.bill_date = None
		self.ma_claim_id = None
		self.patient_name = None
		self.payer = None
		self.claim_amount = None
		self.bill_status = None
		self.claim_id = None
		self.event = None
		self.remark = None
		self.date = datetime.now().date()

	def on_update(self):
		bill_entry_log = frappe.get_doc({'doctype':"Bill Entry Log", "bill":self.bill, "ma_claim_no":self.ma_claim_id, "event":self.event, "date":self.date, "mode_of_submission": self.mode_of_submission, "remark":self.remark})
		self.set_none_value()
		bill_entry_log.insert()
		frappe.db.commit()