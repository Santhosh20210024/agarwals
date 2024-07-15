import frappe
PROJECT_FOLDER = "DrAgarwals"
HOME_PATH = "Home/DrAgarwals"
SHELL_PATH = "private/files"
SUB_DIR = ["Extract", "Transform", "Load", "Bin", "Zip","Settlement Advice"]
INNER_SUB_DIR = ["Error"]
# SITE_PATH = frappe.get_single('Control Panel').site_path
SITE_PATH = "/home/santhoshsivan/agarwals-77-bench/sites/agarwalstest.com"


def construct_file_url(*args):
    list_of_items = []
    for arg in args:
        list_of_items.append(arg)

    formatted_url = '/'.join(list_of_items)
    return formatted_url

def log_error(error):
    error_log = frappe.new_doc('Error Log Record')
    error_log.doctype_name = 'File upload'
    error_log.error_message = str(error)
    error_log.save()

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
            attached_to_doctype = 'DocType'
        template_file = frappe.get_list('File'
                                        ,filters = { 'attached_to_doctype': attached_to_doctype, 'attached_to_name': attached_to_name}
                                        ,pluck='file_url')
        if len(template_file) == 1:
            return template_file[0]
        else:
            return 'Not Found'
    except frappe.exceptions.DoesNotExistError as e:
        log_error(e)
        frappe.db.commit()
        return 'Not Found'
    except Exception as e:
        log_error(e)
        frappe.db.commit()
        return 'System Error'