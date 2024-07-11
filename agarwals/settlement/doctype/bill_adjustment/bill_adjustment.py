import frappe.utils
import frappe
from agarwals.agarwals.doctype import file_records
from agarwals.utils.accounting_utils import is_accounting_period_exist
from frappe.model.document import Document
from agarwals.utils.error_handler import log_error
from datetime import date

class BillAdjustment(Document):
	"""
    A class to represent Bill Adjustments and handle validations and updates before saving the document.
    Custom Methods:
    	-> _handle_invoice_status
    	-> _validate_amount
    	-> _set_posting_date
    	-> _update_posting_date
    """

	def before_save(self):
		"""
        Method to handle operations before save.
        """
		if self.name:
			sales_doc = frappe.get_doc("Sales Invoice", self.name)
			self._handle_invoice_status(sales_doc)
			self._validate_amount(sales_doc)
			self._set_posting_date(sales_doc)

	def _handle_invoice_status(self, sales_doc):
		"""
		Method to handle the invoice status
		"""
		if sales_doc.status == 'Paid':
			self.status = 'Error'
			self.error_remark = 'Paid Bill'
			return
		if sales_doc.status == 'Cancelled':
			self.status = 'Error'
			self.error_remark = 'Cancelled Bill'
			return

	def _validate_amount(self, sales_doc):
		"""
        Validates TDS and disallowance amounts against the outstanding amount of the sales invoice.
        """
		if self.tds > sales_doc.outstanding_amount:
			self.status = 'Error'
			self.error_remark = 'TDS amount is greater than the claim amount'
			return

		if self.disallowance > sales_doc.outstanding_amount:
			self.status = 'Error'
			self.error_remark = 'Disallowance amount is greater than the claim amount'
			return

	def _set_posting_date(self, sales_doc):
		"""
        Sets the posting date based on the status of the sales invoice and payment references.
        """
		try:
			if sales_doc.status == 'Unpaid':
				self._update_posting_date(sales_doc.posting_date)
			elif sales_doc.status == 'Partly Paid':
				payment_reference = frappe.db.get_list('Payment Entry', filters={'custom_sales_invoice': self.name}, fields=['posting_date'], order_by="creation desc")
				if payment_reference:
					self._update_posting_date(payment_reference[0].posting_date)
				else:
					self._update_posting_date(sales_doc.posting_date)
		except Exception as e:
			log_error(str(e), doc='Bill Adjustment', doc_name='New Record')

	def _update_posting_date(self, date_to_check):
		"""
        Updates the posting date based on whether the accounting period exists.
        """
		if is_accounting_period_exist(date_to_check.strftime("%Y-%m-%d")):
			self.posting_date = date.today().strftime("%Y-%m-%d")
		else:
			self.posting_date = date_to_check.strftime("%Y/%m/%d")

	def on_update(self):
		file_records.create(
			file_upload=self.file_upload,
			transform=self.transform,
			reference_doc="Bill Adjustment",
			record=self.name,
			index=self.index
		)