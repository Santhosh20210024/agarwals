# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from agarwals.reconciliation.doctype.sa_downloader_configuration import create_pattern,is_pattern_exists

class SADownloaderConfiguration(Document):
	def autoname(self)->None:
		self.name = self.class_name

	def validate_url_pattern_update(self) -> None:
		previous_url: str = frappe.db.get_value("SA Downloader Configuration", {"name": self.name}, 'website_url')
		if previous_url == self.website_url:
			return
		else:
			new_pattern: str = create_pattern(self.website_url)
			if is_pattern_exists(new_pattern):
				frappe.throw(f"Pattern already exists: {new_pattern}")
			else:
				self.portal_pattern: str = new_pattern

	def before_save(self):
		self.validate_url_pattern_update()



