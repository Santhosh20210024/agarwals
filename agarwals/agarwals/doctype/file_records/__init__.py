import frappe
from agarwals.utils.error_handler import log_error


def create(**kwargs):
    try:
        doc = frappe.new_doc("File Records")
        for key, value in kwargs.items():
            setattr(doc, key, value)
        doc.insert(ignore_permissions=True)
        # doc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        log_error(f"cannot insert File Records due to error: {e}", "File Records", None)
