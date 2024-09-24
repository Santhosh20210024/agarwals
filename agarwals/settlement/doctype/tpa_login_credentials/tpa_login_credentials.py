# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import hashlib

class TPALoginCredentials(Document):

	def update_hash_value(self):
		hash_fileds: str = self.user_name+self.executing_method
		hash_value: str = hashlib.sha1(hash_fileds.encode('utf-8')).hexdigest()
		self.hash: str = hash_value

	def before_save(self):
		self.update_hash_value()
