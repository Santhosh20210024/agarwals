import frappe
import os
from agarwals.utils.error_handler import log_error
from agarwals.utils.file_util import HOME_PATH, SUB_DIR, SHELL_PATH, SITE_PATH, INNER_SUB_DIR, construct_file_url

def get_site_path():
    try:
        return os.path.join(SITE_PATH, SHELL_PATH)
    except Exception as e:
        print(f"Error: {e}")

def get_file_list(filters):
    return frappe.get_all("File", filters = filters, pluck='name')

def create_new_folder(file_name, folder):
	file = frappe.new_doc("File")
	file.file_name = file_name
	file.is_folder = 1
	file.folder = folder
	file.insert(ignore_if_duplicate=True)
	frappe.db.commit()

def get_file_path(parent_folder_item = None, sub_folder_item = None):
    from agarwals.utils.file_util import PROJECT_FOLDER

    path_components = [parent_folder_item]
    if sub_folder_item:
        path_components.append(sub_folder_item)

    COMBINED_PATH = os.path.join(*path_components)
    return os.path.join(get_site_path(), PROJECT_FOLDER, COMBINED_PATH)

def folder_structure_creation():
    from agarwals.utils.file_util import PROJECT_FOLDER
    print("**------ Folder Structure Creating --------**")

    try:
        if not PROJECT_FOLDER:
            while True:
                project_name = input('Please enter the project name (i.e., DrAgarwals, EyeFoundation): ')
                if project_name:
                    PROJECT_FOLDER = project_name.strip()
                    break
        
        if not SITE_PATH or not SHELL_PATH:
            frappe.throw('Tfs control panel site configurations are mandatory to configure')

        if not SUB_DIR or not INNER_SUB_DIR:
            frappe.throw("Please specify the sub directory in control panel:")

        PROJECT_FOLDER_PATH = "".join([get_site_path(), PROJECT_FOLDER])
        if not os.path.exists(PROJECT_FOLDER_PATH):
            os.mkdir(PROJECT_FOLDER_PATH)

        if HOME_PATH not in get_file_list({'is_folder': 1}):
            create_new_folder(PROJECT_FOLDER, "Home")
        
        for sub_item in SUB_DIR:
            print(HOME_PATH, sub_item)
            if construct_file_url(HOME_PATH, sub_item) not in get_file_list({'is_folder': 1}):
                create_new_folder(sub_item, HOME_PATH)
            
            sub_item_path = get_file_path(sub_item)
            os.makedirs(sub_item_path, exist_ok=True)

            for inner_folder_item in INNER_SUB_DIR:
                dir_path = os.path.join(HOME_PATH, sub_item)
                create_new_folder(inner_folder_item, dir_path)

                inner_item_path = get_file_path(sub_item, inner_folder_item)
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