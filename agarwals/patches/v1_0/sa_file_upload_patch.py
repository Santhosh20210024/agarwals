import frappe
from agarwals.utils.error_handler import log_error

def execute():
    frappe.reload_doc("agarwals", "doctype", "File_upload")
    
    # Fetch file upload records
    file_upload = frappe.db.sql(
        "SELECT * FROM `tabFile upload` tfu WHERE is_bot = 0 AND document_type = 'Settlement Advice'", 
        as_dict=True
    )

    for file_record in file_upload:
        try:
            file_upload_record = frappe.get_doc("File upload",file_record.get('name'))
            file_upload_record.update({
                'sa_mail_sent':1
            })
            file_upload_record.save()

        except Exception as error:
            # Log errors encountered during the process
            log_error(
                error='Unable to check the file_upload record {file_name}. Error: {error}'.format(
                    file_name=file_record.get('name'),
                    error=str(error)
                ),
                doc="File Upload",
                doc_name=file_record.get('name')
            )
