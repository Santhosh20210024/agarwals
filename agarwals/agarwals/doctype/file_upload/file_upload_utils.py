import frappe 
from agarwals.utils.error_handler import log_error

@frappe.whitelist()
def is_template_exist(file_doctype, file_name):
    """
    Check if a template exists for the given doctype.
    :return: URL of the template file if found, 'Not Found' if not, 'System Error' on exception
    """
    
    try:
        if not file_name:
            file_name = "File name"
        if file_name == "Manual" :
            file_doctype = file_doctype +".csv"
            template_file = frappe.get_all(
                "File",
                filters={
                    "file_name":file_doctype,
                },
                pluck="file_url"
            )
            if len(template_file) == 1:
                return template_file[0]
        return "Not Found"
    except frappe.exceptions.DoesNotExistError as e:
        log_error(str(e), "File upload")
        return "Not Found"
    except Exception as e:
        log_error(str(e), "File upload")
        return "System Error"
    
def construct_file_url(*args):
    """Construct a file URL from the given path components, handling None values."""
    args = [str(arg) for arg in args if arg is not None]
    formatted_url = "/".join(args)
    return formatted_url