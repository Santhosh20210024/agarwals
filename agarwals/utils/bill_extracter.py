import frappe
from agarwals.utils.error_handler import log_error

class DebtorsExtracter():
   
    def get_attachment(self,doc):
        try:
            comm_doc = frappe.get_doc('Communication',doc)
            attachments =  self.get_file(comm_doc)
            for attachment in attachments:
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
      DebtorsExtracter().get_attachment(doc["name"])
    
