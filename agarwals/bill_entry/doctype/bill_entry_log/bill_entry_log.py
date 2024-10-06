# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
from agarwals.utils.error_handler import log_error
from datetime import datetime
from agarwals.bill_entry.utils import delete_bill_event

class BillEntryLog(Document):
	def validate(self):
		current_date = datetime.now().date()
		event_date = datetime.strptime(self.date, "%Y-%m-%d").date()
		if event_date > current_date:
			log_error(error="Future Date is Not Allowed")
			frappe.throw("Future Date is Not Allowed.")
		if event_date < current_date and (current_date-event_date).days > 7:
			log_error(error="Back Date More than 7 Days is Not Allowed")
			frappe.throw("Back Date More than 7 Days is Not Allowed.")


	def on_update(self):
		try:
			bill_doc = frappe.get_doc("Sales Invoice", self.bill)
			if bill_doc.status != "Cancelled":
				if self.ma_claim_no:
					bill_doc.set("custom_ma_claim_id", self.ma_claim_no)
				if self.event == "Bill Submitted":
					bill_doc.set("custom_mode_of_submission", self.mode_of_submission)
				bill_doc.append('custom_bill_tracker', {'event': self.event, 'date': self.date, 'remark': self.remark})
				bill_doc.submit()
				frappe.db.commit()
		except Exception as e:
			log_error(error=e,doc="Bill Entry",doc_name= self.name)

	def on_trash(self):
		try:
			delete_bill_event(self.bill, self.event, self.date, self.mode_of_submission)
		except Exception as e:
			log_error(error=e, doc="Bill Entry", doc_name=self.name)