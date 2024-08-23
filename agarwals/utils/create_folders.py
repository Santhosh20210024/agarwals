import os
import frappe
from agarwals.utils.error_handler import log_error
from agarwals.utils.file_util import HOME_PATH, SUB_DIR, SHELL_PATH, SITE_PATH, PROJECT_FOLDER, INNER_SUB_DIR, construct_file_url

def get_file_doc_list(filters):
    """Retrieve a list of file names matching the specified filters"""
    try:
        return frappe.get_all("File", filters = filters, pluck='name')
    except Exception as e:
        frappe.throw(f"Error retrieving file list: {e}")

def create_new_folder(file_name, folder):
    """Create a new folder in the frappe file doctype"""
    try:
        file = frappe.new_doc("File")
        file.file_name = file_name
        file.is_folder = 1
        file.folder = folder
        file.insert(ignore_if_duplicate=True)
        frappe.db.commit()
    except Exception as e:
        frappe.throw(f'Error creating new folder: {e}')

def get_file_path(site_path, parent_folder_item = None, sub_folder_item = None):
    """Construct the file path based on the parent and sub-folder items"""

    path_components = [parent_folder_item]
    if sub_folder_item:
        path_components.append(sub_folder_item)

    compined_path = os.path.join(*path_components)
    return construct_file_url(construct_file_url(site_path, SHELL_PATH), PROJECT_FOLDER, compined_path)

def get_required_fields():
    if not PROJECT_FOLDER:
            while True:
                project_name = input("Please enter the project name (i.e., DrAgarwals, EyeFoundation): ")
                if project_name:
                    _PROJECT_FOLDER = project_name.strip()
                    break
    else:
        _PROJECT_FOLDER = PROJECT_FOLDER
    
    if not SITE_PATH:
        while True:
            site_path = input("Please enter the site name (i.e., /home/bench/sites/site-name): ")
            if site_path:
                _SITE_PATH = site_path.strip()
    else:
        _SITE_PATH = SITE_PATH
    
    if not SUB_DIR:
            frappe.throw("Please specify the sub directory in control panel:")
    
    return _PROJECT_FOLDER, _SITE_PATH

def make_dirs(dir, check=True):
    os.makedirs(dir, exist_ok=check)

def create_project_folders():
    """Create the necessary folder structure for a project."""
    
    print("**------ Folder Structure Creating --------**")

    try:
        PROJECT_FOLDER, SITE_PATH = get_required_fields()
        
        PROJECT_FOLDER_PATH = os.path.join(SITE_PATH, PROJECT_FOLDER)
        if not os.path.exists(PROJECT_FOLDER_PATH):
            os.mkdir(PROJECT_FOLDER_PATH)

        if HOME_PATH not in get_file_doc_list({'is_folder': 1}):
            create_new_folder(PROJECT_FOLDER, "Home")
        
        for sub_item in SUB_DIR:
            print(HOME_PATH, sub_item)
            if construct_file_url(HOME_PATH, sub_item) not in get_file_doc_list({'is_folder': 1}):
                create_new_folder(sub_item, HOME_PATH)
            
            sub_item_path = construct_file_url(construct_file_url(SITE_PATH, SHELL_PATH), PROJECT_FOLDER, sub_item)
            make_dirs(sub_item_path)
            for inner_folder_item in INNER_SUB_DIR:
                dir_path = os.path.join(HOME_PATH, sub_item)
                create_new_folder(inner_folder_item, dir_path)

                inner_item_path = construct_file_url(construct_file_url(SITE_PATH, SHELL_PATH), PROJECT_FOLDER, sub_item, inner_folder_item)
                os.makedirs(inner_item_path, exist_ok=True)

        print("**-------- Folder Structure Created --------**")
    except Exception as e:
        frappe.throw(f"Error: {e}")

@frappe.whitelist()
def create_sa_folders():
    path = frappe.get_single("Control Panel").site_path + "/private/files/DrAgarwals/Settlement Advice"
    already_exists = False
    try:
        if os.path.exists(path):
            folder_names = set(frappe.db.sql("SELECT tpa FROM `tabTPA Login Credentials` WHERE is_enable = 1",pluck ="tpa"))
            for name in folder_names:
                folder = path + "/" +name
                if not os.path.exists(folder):
                    os.mkdir(folder)
                else:
                    log_error(error = f"Folder {name} Already Exists")
                    already_exists = True
            return "folder created" if already_exists == False else "folder already exists"
        else:
            return "path not found"
    except Exception as e:
        log_error(error = e)
        return "unexpected error occurs"