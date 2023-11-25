import frappe
import os
from frappe.utils import get_site_name

# Required Agarwals Folders
PROJECT_FOLDER = "DrAgarwals"
ROOT_FOLDER = 'Home/DrAgarwals' 
PARENT_FOLDERS_LIST = ['Extract', 'Transform']
SUB_FOLDERS_LIST = ['Bank', 'Payment_Advice', 'Claimbook', 'Bill', 'Error']

# For Production:  get_site_name(frappe.local.request.host)
SITE_PATH = os.getcwd() + "/agarwals.com" + "/private/files/"

# Examples
# BANK_LIST = ['HDFC','KKBK','KOTAK']
# TPA_LIST = ['ORINTEL']


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

    if ROOT_FOLDER not in get_file_list('all',{'is_folder':1}):
        create_new_folder(PROJECT_FOLDER, "Home")
    
    # Parent Folders at both places
    for parent_folder_item in PARENT_FOLDERS_LIST:
        create_new_folder(parent_folder_item, ROOT_FOLDER)
        
        if not os.path.exists(get_file_path(parent_folder_item)):
            os.mkdir(get_file_path(parent_folder_item))

        # Sub folders
        for sub_folder_item in SUB_FOLDERS_LIST:
            dir = ROOT_FOLDER + "/" + parent_folder_item
            create_new_folder(sub_folder_item, dir)

            if not os.path.exists(get_file_path(parent_folder_item,sub_folder_item)):
                os.mkdir(get_file_path(parent_folder_item,sub_folder_item))

            # if sub_folder_item == "Bank":
            #     for bank_item in BANK_LIST:
            #         create_new_folder(bank_item, dir + "/" + sub_folder_item)

            #         if not os.path.exists(get_file_path(parent_folder_item,sub_folder_item,bank_item)):
            #             os.mkdir(get_file_path(parent_folder_item,sub_folder_item,bank_item))

            # if sub_folder_item == "Debtor_Payments":
            #     for tpa_item in TPA_LIST:
            #         create_new_folder(tpa_item, dir + "/" + sub_folder_item)
                    
            #         if not os.path.exists(get_file_path(parent_folder_item,sub_folder_item,tpa_item)):
            #             os.mkdir(get_file_path(parent_folder_item,sub_folder_item,tpa_item))


    print("-------- File Structure Completed --------")


# def folder_structure_deletion():
#     print("-------- File Structure Deletion --------")
#     dr_agarwals_files = get_file_list('or', [["name", "like", "%DrAgarwals%"],["file_url", "like", "%DrAgarwals%"]])

#     for every_files in dr_agarwals_files:
#         frappe.delete_doc("File",every_files)
#         frappe.db.commit()