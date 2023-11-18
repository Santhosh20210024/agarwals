import frappe
import os
from frappe.utils import get_site_name

# Required Agarwals Folders
ROOT_FOLDER = 'Home/DrAgarwals' 
PARENT_FOLDERS_LIST = ['Upload','InProcessing','Processed','Backup']
SUB_FOLDERS_LIST = ['Bank','Debtor_Payments','Claimbook','Bills']

# For Production:  get_site_name(frappe.local.request.host)
SITE_PATH = os.getcwd() + "/ga.site" + "/private/files/"

# Examples
BANK_LIST = ['HDFC','KKBK','KOTAK']
TPA_LIST = ['ORINTEL']


def get_folders_list():
    folders_list = frappe.get_all("File", filters={'is_folder':1}, pluck='name')
    return folders_list

# Frappe default creation method
def create_new_folder(file_name, folder):
	file = frappe.new_doc("File")
	file.file_name = file_name
	file.is_folder = 1
	file.folder = folder
	file.insert(ignore_if_duplicate=True)
	frappe.db.commit()


# Folder only
"""
Sample File Doctype Output

['Home',                                                                                                 
'Home/Attachments',                                                                                     
'Home/Agarwals',                                                                                        
'Home/test',                                                                                            
'Home/X',                                                                                               
'f4fea994f6',                                                                                           
'Home/Agarwals/HDFC']          """

def folder_structure_creation():
    print("Folder Structure Initialization")

    # Agarwals directory
    if not os.path.exists(SITE_PATH + ROOT_FOLDER.split("/")[1]):
        os.mkdir(SITE_PATH + ROOT_FOLDER.split("/")[1])

    if ROOT_FOLDER not in get_folders_list():
        create_new_folder(ROOT_FOLDER.split("/")[1], ROOT_FOLDER.split("/")[0])
    
    # Parent Folders at both places
    for parent_folder_item in PARENT_FOLDERS_LIST:
        create_new_folder(parent_folder_item, ROOT_FOLDER)
        if not os.path.exists(SITE_PATH + ROOT_FOLDER.split("/")[1] + "/" + parent_folder_item):
            os.mkdir(SITE_PATH + ROOT_FOLDER.split("/")[1]+ "/" + parent_folder_item)

    # Sub folders
    for sub_folder_item in SUB_FOLDERS_LIST:

        upload_dir = ROOT_FOLDER + "/" + PARENT_FOLDERS_LIST[0]
        create_new_folder(sub_folder_item, upload_dir)

        if not os.path.exists(SITE_PATH + ROOT_FOLDER.split("/")[1] + "/" + PARENT_FOLDERS_LIST[0] + "/" + sub_folder_item):
            os.mkdir(SITE_PATH + ROOT_FOLDER.split("/")[1]+ "/" + PARENT_FOLDERS_LIST[0] + "/" + sub_folder_item)

        if sub_folder_item == "Bank":
            for bank_item in BANK_LIST:
                create_new_folder(bank_item, upload_dir + "/" + sub_folder_item)

                if not os.path.exists(SITE_PATH + ROOT_FOLDER.split("/")[1] + "/" + PARENT_FOLDERS_LIST[0] + "/" + sub_folder_item + "/" + bank_item):
                    os.mkdir(SITE_PATH + ROOT_FOLDER.split("/")[1] + "/" + PARENT_FOLDERS_LIST[0] + "/" + sub_folder_item + "/" + bank_item)

        if sub_folder_item == "Debtor_Payments":
            for tpa_item in TPA_LIST:
                create_new_folder(tpa_item, upload_dir + "/" + sub_folder_item)
                
                if not os.path.exists(SITE_PATH + ROOT_FOLDER.split("/")[1] + "/" + PARENT_FOLDERS_LIST[0] + "/" + sub_folder_item + "/" + tpa_item):
                    os.mkdir(SITE_PATH + ROOT_FOLDER.split("/")[1] + "/" + PARENT_FOLDERS_LIST[0] + "/" + sub_folder_item + "/" + tpa_item)


    print("Folder Structure Completed")

#Uninsallation file delete
# Let to be Done

