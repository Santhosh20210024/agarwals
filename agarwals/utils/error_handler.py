import frappe

def log_error(error,doc=None,doc_name=None):
    error_log = frappe.new_doc('Error Record Log')
    error_log.set('doctype_name', doc)
    error_log.set('reference_name', doc_name)
    error_log.set('error_message', error)
    error_log.save()
    return error_log