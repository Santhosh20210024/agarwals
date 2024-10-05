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
		bill_entry_log = frappe.new_doc("Bill Entry Log")
		bill_entry_log.set("bill",self.bill)
		bill_entry_log.set("ma_claim_no", self.ma_claim_id)
		bill_entry_log.set("event", self.event)
		bill_entry_log.set("date", self.date)
		bill_entry_log.set("mode_of_submission", self.mode_of_submission)
		bill_entry_log.set("remark", self.remark)
		self.set_none_value()
		bill_entry_log.save()
		frappe.db.commit()