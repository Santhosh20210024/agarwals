import frappe
from agarwals.utils.error_handler import log_error


def create(**kwargs):
    doc_name = "File Records"
    try:
        if frappe.db.exists(doc_name, kwargs["file_upload"]+"-"+kwargs["reference_doc"]+"-"+kwargs["record"]):
            return None
        doc = frappe.new_doc(doc_name)
        for key, value in kwargs.items():
            setattr(doc, key, value)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        log_error(f"cannot insert File Records due to error: {e}", doc_name, None)