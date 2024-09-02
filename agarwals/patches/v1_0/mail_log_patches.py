import frappe
from agarwals.utils.error_handler import log_error

def execute():
    frappe.reload_doc("agarwals", "doctype", "mail_log")
    
    # Fetch file upload records
    file_upload = frappe.db.sql(
        "SELECT * FROM `tabFile upload` tfu WHERE is_bot = 0 AND document_type = 'Settlement Advice'", 
        as_dict=True
    )

    for file_record in file_upload:
        try:
            # Create a new Mail log document
            mail_log_record = frappe.new_doc('Mail log')
            
            mail_log_record.update({
                'file_upload': file_record.get('name'),
                'file_type': file_record.get('document_type'),
                'status': "Open"
                })

            mail_log_record.save()

        except Exception as error:
            # Log errors encountered during the process
            log_error(
                error='Unable to Create Mail log for file record {file_name}. Error: {error}'.format(
                    file_name=file_record.get('name'),
                    error=str(error)
                ),
                doc="File Upload",
                doc_name=file_record.get('name')
            )
