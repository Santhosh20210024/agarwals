# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from agarwals.utils.index_update import update_index

class IndexUpdation(Document):
    
	def before_save(self):
            update_index(self.name)