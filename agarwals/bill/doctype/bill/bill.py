# Copyright (c) 2023, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document



class Bill(Document):
	def before_save(self):
		self.cost_center = self.branch + " - A"



