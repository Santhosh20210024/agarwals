# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt
import frappe.utils
import frappe
from frappe.model.document import Document

class BillAdjustment(Document):
	def before_save(self):
		if not self.posting_date:
			if self.name:
				sales_doc = frappe.get_doc('Sales Invoice', self.name)
				if sales_doc.status == 'Unpaid':
					self.status = 'Error'
					self.error_remark = 'Unpaid Bill'
				elif sales_doc.status == 'Paid':
					self.status = 'Error'
					self.error_remark = 'Paid Bill'
				if sales_doc.status == 'Partly Paid':
					payment_reference = frappe.db.get_list('Payment Entry',filters={'custom_sales_invoice': self.name},fields=['posting_date'], order_by="creation asc")
					self.posting_date = payment_reference[0]['posting_date'].strftime("%Y/%m/%d")
