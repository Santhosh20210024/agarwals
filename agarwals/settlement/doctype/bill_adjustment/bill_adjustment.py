import frappe
from agarwals.agarwals.doctype import file_records
from agarwals.utils.accounting_utils import update_posting_date
from frappe.model.document import Document
from agarwals.utils.error_handler import log_error


class BillAdjustment(Document):
	"""A class to represent Bill Adjustments and handle validations and 
	updates before insert the document"""

	def before_insert(self):
		"""Method to handle operations before save"""
		if self.name:
			sales_doc = frappe.get_doc("Sales Invoice", self.name)
			self._handle_invoice_status(sales_doc)
			if self.status == 'Error':
				return
			self._validate_amount(sales_doc)
			self._set_posting_date(sales_doc)

	def _handle_invoice_status(self, sales_doc):
		"""Method to handle the invoice status"""
		if sales_doc.status in ['Paid', 'Cancelled']:
			self.status = 'Error'
			self.error_remark = f'{sales_doc.status} Bill'

	def _validate_amount(self, sales_doc, tolerance=1):
		"""Validates TDS and disallowance amounts against the outstanding amount of the sales invoice,
		allowing for a small tolerance to account for decimal differences"""
		outstanding_amount = float(sales_doc.outstanding_amount)
		error_messages = []

		if float(self.tds) - outstanding_amount > tolerance:
			error_messages.append('TDS amount is greater than the outstanding amount')

		if float(self.disallowance) - outstanding_amount > tolerance:
			error_messages.append('Disallowance amount is greater than the outstanding amount')

		if error_messages:
			self.status = 'Error'
			self.error_remark = "\n".join(error_messages)

	def _set_posting_date(self, sales_doc):
		"""Sets the posting date based on the status of the sales invoice and payment references"""
		try:
			if sales_doc.status == 'Unpaid':
				self.posting_date = update_posting_date(sales_doc.posting_date)
			elif sales_doc.status == 'Partly Paid':
				payment_reference = frappe.db.get_list('Payment Entry', filters={'custom_sales_invoice': self.name}, fields=['posting_date'], order_by="creation desc")
				if payment_reference:
					self.posting_date = update_posting_date(payment_reference[0].posting_date)
				else:
					self.posting_date = update_posting_date(sales_doc.posting_date)
		except Exception as e:
			log_error(str(e), doc='Bill Adjustment', doc_name='New Record')

	def on_update(self):
		file_records.create(
			file_upload=self.file_upload,
			transform=self.transform,
			reference_doc="Bill Adjustment",
			record=self.name,
			index=self.index
		)