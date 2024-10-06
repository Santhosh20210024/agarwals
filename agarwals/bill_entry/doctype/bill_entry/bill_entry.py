# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from agarwals.bill_entry.utils import update_bill_event

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
		self.mode_of_submission = None
		self.date = datetime.now().date()

	def on_update(self):
		update_bill_event(self.bill, self.event, self.date, self.mode_of_submission, self.remark, self.ma_claim_id)
		self.set_none_value()