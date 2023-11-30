import frappe
from agarwals.utils.import_bank_statement import import_bank_statement

@frappe.whitelist()
def loading():
	transformed_files = frappe.get_list('File Upload',filters={'status':'Transformed'},fields=['bank','bank_account','transformed_file_url','name'])
	for every_file in transformed_files:
		bank = every_file.bank
		bank_account = every_file.bank_account
		transformed_file_url = every_file.transformed_file_url
		import_bank_statement(bank = bank,bank_account = bank_account,attached_file= transformed_file_url)

		file_doc = frappe.get_doc("File Upload",every_file["name"])
		file_doc.status = "Loaded"
		file_doc.save()
	return "Success"