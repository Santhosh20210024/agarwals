import frappe

def log_error(error, doc=None, doc_name=None, status='Error'):
    if doc_name and len(doc_name) > 140:
        doc_name = doc_name[:139]
        
    error_log = frappe.get_doc({
        'doctype': 'Error Record Log',
        'doctype_name': doc,
        'reference_name': doc_name,
        'error_message': error,
        'status': status
    })
    
    error_log.insert(ignore_permissions=True)
