import frappe
from agarwals.utils.error_handler import log_error

class DebtorsExtracter():
    
    FILE_FORMAT = frappe.get_single('Control Panel').allowed_file_extensions.split(",")
    
    
    def process_communication_files(self,doc):
        try:
            comm_doc = frappe.get_doc('Communication',doc)
            attachments =  self.get_file(comm_doc)
            for attachment in attachments:
                if self.validate_extension(attachment['file_url']):
                    create_file_upload(attachment)
            comm_doc.status = 'Closed'
            comm_doc.save()
            frappe.db.commit()
        except Exception as e:
            log_error(f"error While Processing File Upload Bill - {e}",doc="Communication")
            
    def get_file(self,doc):
        attachments = frappe.get_all('File',filters ={'attached_to_doctype': 'Communication','attached_to_name': doc.name})
        attachment_details = []
        for attachment in attachments:
            file_doc = frappe.get_doc('File', attachment.name)
            attachment_details.append({
            'file_url': file_doc.file_url
            })
        return attachment_details
    
    def validate_extension(self,attachment):
        return any(attachment.endswith(ext.lower()) for ext in self.FILE_FORMAT)
        
            
@frappe.whitelist()
def create_file_upload(attachment):
	file_upload_doc=frappe.new_doc("File upload")
	file_upload_doc.file_format= 'EXCEL'
	file_upload_doc.document_type= "Debtors Report"
	file_upload_doc.upload= attachment['file_url']
	file_upload_doc.save(ignore_permissions=True)
	
 
@frappe.whitelist()       
def process(doc):
    doc = eval(doc)
    if doc["sent_or_received"] !='Sent':
      DebtorsExtracter().process_communication_files(doc["name"])
    
