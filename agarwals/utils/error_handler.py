import frappe

def log_error(error, doc=None, doc_name=None, status='ERROR'):
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
    return error_log

class CGException(Exception):
    """Custom exception for handling bank transaction errors."""
    
    def __init__(self, method_name: str, message: str):
        self.method_name=method_name
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.method_name}: {self.message}"
