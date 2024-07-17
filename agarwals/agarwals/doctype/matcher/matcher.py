# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from agarwals.utils.payment_utils import update_error, get_company_account

class Matcher(Document):
	def before_save(self):
		ref_doc = frappe.get_doc("Settlement Advice", self.settlement_advice)
		if not self.settlement_advice:
			ref_doc = frappe.get_doc("ClaimBook", self.claimbook)
		self.file_upload = ref_doc.file_upload
		self.transform = ref_doc.transform
		self.index = ref_doc.index

	def on_update(self):
		error = None
		if len(self.bank_transcation) < 4:
			error = "Reference number should be minimum of 5 digits"
		if self.deposit < 8:
			error = "deposit amount should be greater than 8"
		if not self.date:
			error = "Bank date is Null"
		if not self.settled_amount:
			error = 'Settled Amount Should Not Be Zero'
		if float(self.settled_amount) < 0 or float(self.tds_amount) < 0 or float(self.disallowance_amount) < 0:
			error = 'Amount Should Not Be Negative'
		if self.bt_status == 'Reconciled':  # Already Reconciled
			error = 'Already Reconciled'
		if self.bt_status not in ['Pending', 'Unreconciled']:
			error = 'Status Should be other then Pending, Unreconciled'
		if self.si_status == 'Cancelled':
			error = 'Cancelled Bill'
		if self.si_status == 'Paid':
			error = 'Already Paid Bill'
		if self.si_total < (self.settled_amount + self.tds_amount + self.disallowance_amount):
			error = 'Claim amount lesser than the cumulative of other amounts'
		if error:
			update_error(self, error)
		self.company_bank_account = get_company_account(self.bt_bank_account)
