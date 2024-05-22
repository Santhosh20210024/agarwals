# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class SADownloaderConfiguration(Document):
	def autoname(self):
		self.name = self.class_name

