import frappe

def get_doc_fields(required = None):
	meta = frappe.get_meta("File Upload")
	fieldnames = [df.fieldname for df in meta.get("fields")]
	if required:
		required_fieldnames = [file_items  for file_items in fieldnames if required in file_items]
		return required_fieldnames
	return fieldnames