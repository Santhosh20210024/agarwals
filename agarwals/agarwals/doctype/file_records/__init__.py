import frappe
from agarwals.utils.error_handler import log_error


def update(**kwargs):
    try:
        doc = frappe.new_doc("File Records")
        doc.insert(ignore_permissions=True)
        for key, value in kwargs.items():
            setattr(doc, key, value)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return doc
    except Exception as e:
        log_error(f"cannot insert File Records due to error: {e}", "File Records", None)
