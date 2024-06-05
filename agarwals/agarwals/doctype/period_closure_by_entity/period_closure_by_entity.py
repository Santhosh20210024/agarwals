# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt
import frappe.utils
# import frappe
from datetime import datetime,date
from frappe.model.document import Document

class PeriodClosurebyEntity(Document):
	def get_last_posted_date(self):
		last_posted_doc = frappe.db.get_list("Period Closer by Entity", fields="*", filters={'entity': self.entity},order_by="posting_date desc")
		last_posted_date = last_posted_doc[0].posting_date if last_posted_doc and last_posted_doc[0].name!=self.name else None
		return last_posted_date

	def on_update(self):
		last_posted_date = self.get_last_posted_date()
		if self.entity and last_posted_date and not self.posting_date:
			self.last_closed_date=last_posted_date

	def validate(self):
		last_posted_date = self.get_last_posted_date()
		if self.posting_date:
			if last_posted_date:
				if last_posted_date >= datetime.strptime(self.posting_date, '%Y-%m-%d').date():
					frappe.msgprint("Posting date must be always greater than 'Last Closing Date'","Error",True,indicator="red")
			# 	if datetime.strptime(self.posting_date, '%Y-%m-%d').date() > date.today():
			# 		frappe.msgprint("Posting date cannot be Future Date", "Error", True,indicator="red")
			# else:
			# 	if datetime.strptime(self.posting_date, '%Y-%m-%d').date() > date.today():
			# 		frappe.msgprint("Posting date cannot be Future Date", "Error", True,indicator="red")

