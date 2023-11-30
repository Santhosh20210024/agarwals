# Copyright (c) 2023, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from agarwals.utils.importation_and_doc_creation import create_sales_invoice


class DebtorsReport(Document):
	def before_save(self):
		#Sales Invoice creation before saving the debtors
		if self.region == "Agarwals - A":
			self.region = self.branch
		self.region = self.region.replace(" - A", "")
		if self.status != "CANCELLED":
			sales_invoice_item = [{'item_code': 'Claim', 'rate': self.claim_amount, 'qty': 1}]
			sales_invoice_field_and_value = {'entity': self.company, 'region': self.region,
											 'cost_center': self.branch, 'name': self.bill_no,
											 'date': self.bill_date, 'items': sales_invoice_item,
											 'customer': self.payer}
			creation_status = create_sales_invoice(sales_invoice_field_and_value)
			if creation_status == "success":
				return "Success"
			else:
				return creation_status

