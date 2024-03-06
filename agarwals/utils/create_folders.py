import frappe
import os

from agarwals.utils.file_util import HOME_PATH,SUB_DIR,SITE_PATH,PROJECT_FOLDER,INNER_SUB_DIR

#SITE PATH
SITE_PATH = os.getcwd() + frappe.get_site_path()[1:] + "/private/files/"

def get_file_list(filter_type,dict):
    if filter_type == "all":
        folders_list = frappe.get_all("File", filters = dict, pluck='name')
    if filter_type == "or":
        folders_list = frappe.get_all("File", or_filters = dict, pluck='name')
    return folders_list

def create_new_folder(file_name, folder):
	file = frappe.new_doc("File")
	file.file_name = file_name
	file.is_folder = 1
	file.folder = folder
	file.insert(ignore_if_duplicate=True)
	frappe.db.commit()

def get_file_path(parent_folder_item = None,sub_folder_item = None,bank_item = None,tpa_item = None):
    path_components = []
    if parent_folder_item:
        path_components.append(parent_folder_item)

    if sub_folder_item:
        path_components.append(sub_folder_item)
    
    COMBINED_PATH = "/".join(path_components)
    file_path = SITE_PATH + PROJECT_FOLDER + "/" + COMBINED_PATH
    return file_path

def folder_structure_creation():
    print("------ File Structure Initialization --------")

    # Agarwals directory
    if not os.path.exists(SITE_PATH + PROJECT_FOLDER):
        os.mkdir(SITE_PATH + PROJECT_FOLDER)

    if HOME_PATH not in get_file_list('all',{'is_folder':1}):
        create_new_folder(PROJECT_FOLDER, "Home")
    
    # Parent Folders at both places
    for parent_folder_item in SUB_DIR:
        create_new_folder(parent_folder_item, HOME_PATH)
        
        if not os.path.exists(get_file_path(parent_folder_item)):
            os.mkdir(get_file_path(parent_folder_item))

        # Sub folders
        for sub_folder_item in INNER_SUB_DIR:
            dir = HOME_PATH + "/" + parent_folder_item
            create_new_folder(sub_folder_item, dir)

            if not os.path.exists(get_file_path(parent_folder_item,sub_folder_item)):
                os.mkdir(get_file_path(parent_folder_item,sub_folder_item))

    print("-------- File Structure Completed --------")