import frappe 
from agarwals.utils.error_handler import log_error
from frappe.utils.xlsxutils import build_xlsx_response

@frappe.whitelist()


def download_template(file_doctype,file_name):
    try:
        file_doctype = file_doctype.strip() if file_doctype else None
        if not file_name:
            file_name = "File name"
        if file_doctype == "Settlement Advice":
            conf_doc = frappe.get_single("Settlement Advice Configuration")
            headers =eval(conf_doc.columns_for_validation)
            return build_xlsx_response([headers.get(file_name)],file_doctype)
        else :   
            conf_doc = frappe.get_doc("Data Loading Configuration",{file_doctype})
            header_list =eval(conf_doc.columns_for_validation)
            return build_xlsx_response([header_list],file_doctype)
    except frappe.exceptions.DoesNotExistError as e:
        log_error(str(e), "File upload")
    
    
def construct_file_url(*args):
    """Construct a file URL from the given path components, handling None values."""
    args = [str(arg) for arg in args if arg is not None]
    formatted_url = "/".join(args)
    return formatted_url