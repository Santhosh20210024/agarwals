import frappe
from agarwals.utils.error_handler import log_error


class DebtorsExtractor:

    FILE_FORMAT = frappe.get_single("Control Panel").allowed_file_extensions.split(",")

    def process_communication_files(self, doc):
        try:
            comm_doc = frappe.get_doc("Communication", doc)
            attachments = self.get_file(comm_doc)
            for attachment in attachments:
                attachment = frappe.get_doc('File',attachment['name'])
                if self.validate_extension(attachment.file_type):
                    create_file_upload(attachment)
            comm_doc.status = "Closed"
            comm_doc.save()
            frappe.db.commit()
        except Exception as e:
            log_error(
                f"error While Processing File Upload Bill - {e}", doc="Communication"
            )

    def get_file(self, doc):
        attachments = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Communication",
                "attached_to_name": doc.name,
            },
        )
        return attachments

    def validate_extension(self, file_type):
        return file_type in self.FILE_FORMAT


@frappe.whitelist()
def create_file_upload(attachment):
    file_upload_doc = frappe.new_doc("File upload")
    file_upload_doc.file_format = "EXCEL"
    file_upload_doc.document_type = "Debtors Report"
    file_upload_doc.upload = attachment["file_url"]
    file_upload_doc.save(ignore_permissions=True)


@frappe.whitelist()
def process(doc):
        DebtorsExtractor().process_communication_files(doc)
