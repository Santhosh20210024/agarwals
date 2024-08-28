# Copyright (c) 2023, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from agarwals.agarwals.doctype import file_records
from agarwals.utils.accounting_utils import get_abbr




class Bill(Document):
	def before_save(self):
		self.cost_center = self.branch + " - " + get_abbr()

	def on_update(self):
		file_records.create(file_upload = self.file_upload, transform = self.transform, reference_doc = "Bill", record = self.name, index = self.index)



