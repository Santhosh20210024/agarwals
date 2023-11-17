import frappe
# import pandas
from frappe.model.document import Document

class FileUpload(Document):
	def validate_fields(self):
		if self.type == None or self.type == "":
			frappe.throw("Select Type")
			return

		else:
			if self.type == "Bank Statement":
				if self.bank_account == None:
					frappe.throw("Select Bank Account")
				if self.upload == None:
					frappe.throw("Should Upload File")

			if self.type == "Debtor Statement":
				if self.bank_account == None:
					frappe.throw("Select Debtors")
				if self.upload == None:
					frappe.throw("Should Upload File")

			else:
				if self.upload == None:
					frappe.throw("Should Upload File")


	def validate(self):
		self.validate_fields()
		self.check_valid_bank_file()

	
	def check_valid_bank_file(self):
		pass


