# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt
from agarwals.agarwals.doctype import file_records
import frappe
from frappe.model.document import Document

class BankTransactionStaging(Document):
	def on_update(self):
		file_records.create(is_commit=False, file_upload=self.file_upload, transform=self.transform, reference_doc="Bank Transaction Staging",
							record=self.name, index = self.index)
