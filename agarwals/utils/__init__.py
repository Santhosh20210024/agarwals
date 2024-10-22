import frappe

class DatabaseUtils:
    @staticmethod
    def update_doc(doctype, name,is_submittable = False, **kwargs):
        """Update a document in the database."""
        doc = frappe.get_doc(doctype, name)
        for key, value in kwargs.items():
            setattr(doc, key, value)
        doc.save(ignore_permissions=True)
        if is_submittable:
            doc.submit()

    @staticmethod
    def clear_doc(doctype, name):
        """Cancel and delete a document."""
        frappe.get_doc(doctype, name).cancel()
        frappe.delete_doc(doctype, name, ignore_permissions=True)
        frappe.db.commit()