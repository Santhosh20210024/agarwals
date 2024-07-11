# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt
import frappe.utils
import frappe
from agarwals.agarwals.doctype import file_records
from frappe.model.document import Document
import datetime
from datetime import date

class BillAdjustment(Document):
	def before_save(self):
		if self.name:
			sales_doc = frappe.get_doc("Sales Invoice", self.name)

			# Invoice Status Operation
			if sales_doc.status == 'Paid':
				self.status = 'Error'
				self.error_remark = 'Paid Bill'
				return

			if self.tds > sales_doc.total:
				self.status = 'Error'
				self.error_remark = 'TDS amount is greater than the claim amount'
				return

			if self.disallowance > sales_doc.total:
				self.status = 'Error'
				self.error_remark = 'Disallowance amount is greater than the claim amount'
				return

			# Posting Date Operation
			if sales_doc:
				if sales_doc.status == 'Unpaid':
					if sales_doc.posting_date < datetime.date(2024,4,1):
						self.posting_date = date.today().strftime("%Y-%m-%d")
						return
					else:
						self.posting_date = sales_doc.posting_date.strftime("%Y/%m/%d")
						return

				if sales_doc.status == 'Partly Paid':
					payment_reference = frappe.db.get_list('Payment Entry',filters={'custom_sales_invoice': self.name},fields=['posting_date'], order_by="creation desc")
					if payment_reference[0].posting_date < datetime.date(2024,4,1):
						self.posting_date = date.today().strftime("%Y-%m-%d")
						return
					else:
						self.posting_date = payment_reference[0].posting_date.strftime("%Y/%m/%d")
						return

	def on_update(self):
		file_records.create(file_upload=self.file_upload, transform=self.transform, reference_doc="Bill Adjustment",
							record=self.name, index = self.index)
