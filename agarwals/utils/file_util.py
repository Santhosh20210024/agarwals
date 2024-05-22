import frappe
PROJECT_FOLDER = "DrAgarwals"
HOME_PATH = "Home/DrAgarwals"
SHELL_PATH = "private/files"
SUB_DIR = ["Extract", "Transform", "Load", "Bin", "Zip"]
INNER_SUB_DIR = ["Error"]
#SITE_PATH = frappe.get_single('Control Panel').site_path
SITE_PATH = "/home/frappe/frappe-bench/sites/agarwals.claimgenie.ai"


def construct_file_url(*args):
    list_of_items = []
    for arg in args:
        list_of_items.append(arg)

    formatted_url = '/'.join(list_of_items)
    return formatted_url
