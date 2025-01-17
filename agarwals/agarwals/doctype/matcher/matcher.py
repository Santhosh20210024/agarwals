# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from agarwals.utils.reconciliation_utils import update_error, get_company_account

class Matcher(Document):
	def validate_matcher(self) -> bool:
		error: str = ''
		if not self.bank_transaction:
			error = "No Bank Transaction"
		elif len(self.bank_transaction) < 4:
			error = "Reference number should be minimum of 5 digits"
		elif self.deposit < 8:
			error = "deposit amount should be greater than 8"
		elif not self.bt_date:
			error = "Bank date is Null"
		elif not self.settled_amount:
			error = 'Settled Amount Should Not Be Zero'
		elif float(self.settled_amount) < 0 or float(self.tds_amount) < 0 or float(self.disallowance_amount) < 0:
			error = 'Amount Should Not Be Negative'
		elif self.bt_status == 'Reconciled' or self.bt_status == 'Settled':  # Already Reconciled
			error = 'Already Reconciled'
		elif self.bt_status == 'Cancelled':
			error = 'Bank transaction is Cancelled'
		elif self.si_status == 'Cancelled':
			error = 'Cancelled Bill'
		elif self.si_status == 'Paid':
			error = 'Already Paid Bill'
		if error:
			update_error(self, error)
			return False
		return True

	def before_save(self):
		if self.status != "Open":
			return
		if not self.validate_matcher():
			return
		if not self.settlement_advice:
			ref_doc = frappe.get_doc("ClaimBook", self.claimbook)
		else:
			ref_doc = frappe.get_doc("Settlement Advice", self.settlement_advice)
		self.file_upload = ref_doc.file_upload
		self.transform = ref_doc.transform
		self.index = ref_doc.index
		if self.bt_bank_account:
			self.company_bank_account = get_company_account(self.bt_bank_account)

