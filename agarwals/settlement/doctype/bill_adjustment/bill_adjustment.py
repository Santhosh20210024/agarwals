# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt
import frappe.utils
# import frappe
from frappe.model.document import Document

class BillAdjustment(Document):
	def before_save(self):
		if not self.posting_date:
			self.posting_date=frappe.utils.nowdate()
