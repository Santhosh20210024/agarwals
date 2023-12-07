# Copyright (c) 2023, Agarwals and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PhysicalClaimSubmission(Document):
	def before_save(self):
		#For Updating submission date in Debtors report
		bill_no_array = self.bill_list
		for bill_no in bill_no_array:
			debtors_report = frappe.get_doc('Bill',bill_no)
			debtors_report.set('submission_date',self.submission_date)
			debtors_report.save()

