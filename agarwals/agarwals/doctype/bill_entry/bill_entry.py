# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
from agarwals.utils.error_handler import log_error
from datetime import datetime

class BillEntry(Document):
	def validate(self):
		current_date = datetime.now().date()
		event_date = datetime.strptime(self.event_date, "%Y-%m-%d").date()
		if event_date > current_date:
			log_error(error="Future Date is Not Allowed")
			frappe.throw("Future Date is Not Allowed.")
		if event_date < current_date and (current_date-event_date).days > 7:
			log_error(error="Back Date More than 7 Days is Not Allowed")
			frappe.throw("Back Date More than 7 Days is Not Allowed.")

	def update_bill_event(self, bill):
		bill_doc = frappe.get_doc("Sales Invoice",bill)
		if bill_doc.status != "Cancelled":
			if self.event_type == "Bill Submitted":
				bill_doc.set("custom_mode_of_submission",self.mode_of_submission)
			bill_doc.append('custom_bill_tracker', {'event': self.event_type, 'date': self.event_date, 'remark':self.remarks})
			bill_doc.submit()
			frappe.db.commit()

	def delete_bill_event(self, bill):
		bill_tracker_list = frappe.get_all("Bill Tracker",filters={'event':self.event_type,'date':self.event_date, 'parent':bill},pluck='name')
		for bill_tracker in bill_tracker_list:
			if self.mode_of_submission:
				frappe.db.set_value("Sales Invoice",bill,"custom_mode_of_submission","")
			bill_tracker = frappe.get_doc('Bill Tracker',bill_tracker)
			bill_tracker.cancel()
			bill_tracker.delete(ignore_permissions=True)
			frappe.db.commit()

	def after_save(self):
		try:
			self.update_bill_event(self.bill)
		except Exception as e:
			log_error(error=e,doc="Bill Entry",doc_name= self.name)

	def on_trash(self):
		try:
			self.delete_bill_event(self.bill)
		except Exception as e:
			log_error(error=e, doc="Bill Entry", doc_name=self.name)