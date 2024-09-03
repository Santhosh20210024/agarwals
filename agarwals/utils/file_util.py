import frappe
import os
from agarwals.utils.error_handler import log_error

control_panel = frappe.get_single("Control Panel")
PROJECT_FOLDER = control_panel.get("project_folder", None)
HOME_PATH = f"Home/{PROJECT_FOLDER}"
SITE_PATH = control_panel.get("site_path", None)
SHELL_PATH = "private/files"
SUB_DIR = [
    "Extract",
    "Transform",
    "Load",
    "Bin",
    "CheckList",
    "Settlement Advice",
    "Zip",
]
INNER_SUB_DIR = ["Error"]

def construct_file_url(*args):
    """Construct a file URL from the given path components, handling None values."""
    args = [str(arg) for arg in args if arg is not None]
    formatted_url = "/".join(args)
    return formatted_url
  
@frappe.whitelist()
def is_template_exist(attached_to_name, attached_to_doctype):
    """
    Check if a template exists for the given doctype.

    :param attached_to_name: Name of the document the file is attached to
    :param attached_to_doctype: Type of the document the file is attached to (default: 'DocType')
    :return: URL of the template file if found, 'Not Found' if not, 'System Error' on exception
    """
    try:
        if not attached_to_doctype:
            attached_to_doctype = "DocType"
        template_file = frappe.get_list(
            "File",
            filters={
                "attached_to_doctype": attached_to_doctype,
                "attached_to_name": attached_to_name,
            },
            pluck="file_url",
        )
        if len(template_file) == 1:
            return template_file[0]
        else:
            return "Not Found"
    except frappe.exceptions.DoesNotExistError as e:
        log_error(str(e), "File upload")
        return "Not Found"
    except Exception as e:
        log_error(str(e), "File upload")
        return "System Error"
