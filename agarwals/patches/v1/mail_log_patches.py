import frappe
from agarwals.utils.error_handler import log_error

def execute():
    frappe.reload_doc("agarwals", "doctype", "mail_log")
    file_upload = frappe.db.sql(
        "SELECT * FROM `tabFile upload` tfu WHERE is_bot = 0 AND document_type = 'Settlement Advice'", 
        as_dict=True
    )

    for file_record in file_upload:
        try:
            # Create a new Mail log document
            mail_log_record = frappe.new_doc('Mail log')
            mail_log_params = {
                'file_upload': file_record['name'],
                'file_type': file_record['document_type'],
                'status' : "Open" 
            }

            # Set the values for the new Mail log document
            for key, value in mail_log_params.items():
                mail_log_record.set(key, value)

            # Save and submit the new Mail log document after setting all fields
            mail_log_record.insert(ignore_permissions=True)
            mail_log_record.submit()

        except Exception as error:
            # Log errors encountered during the process
            log_error(error='Unable to Create Mail log ' + str(error), doc="File Upload", doc_name=file_record['name'])
            
