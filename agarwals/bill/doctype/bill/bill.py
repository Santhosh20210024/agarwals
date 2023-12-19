# Copyright (c) 2023, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from agarwals.utils.importation_and_doc_creation import create_sales_invoice
from agarwals.utils.splitter import splitter
import pandas as pd


class Bill(Document):
	def before_save(self):
		# Sales Invoice creation before saving the debtors
		if self.region == "Dr Agarwals Eye Hospital - A":
			self.region = self.branch

		self.region = self.region.replace(" - A", "")


		# splitter('/home/balamurugan/agarwals-bench/sites/agarwals.com/private/files/DrAgarwals/Extract/total_debtors.xlsx','Bill')



