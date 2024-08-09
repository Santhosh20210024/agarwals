# Copyright (c) 2023, Agarwals and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from agarwals.agarwals.doctype import file_records

class SettlementAdvice(Document):
	def on_update(self):
		file_records.create(file_upload=self.file_upload, transform=self.transform, reference_doc=self.doctype,
							record=self.name, index = self.index)


