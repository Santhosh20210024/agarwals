import os
import frappe
from agarwals.utils.error_handler import log_error
import shutil
from agarwals.utils.file_util import (
    SUB_DIR,
    SHELL_PATH,
    SITE_PATH,
    PROJECT_FOLDER,
    INNER_SUB_DIR,
    construct_file_url,
)


def get_file_doc_list(filters):
    """Retrieve a list of file names matching the specified filters"""
    try:
        return frappe.get_all("File", filters=filters, pluck="name")
    except Exception as e:
        frappe.throw(f"Error while retrieving file list: {e}")


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
        frappe.throw(f"Error while creating new folder: {e}")


def set_control_panel(PROJECT_FOLDER, SITE_PATH):
    """Setting up the default values in control panel"""
    control_panel_doc = frappe.get_single("Control Panel")
    control_panel_doc.project_folder = PROJECT_FOLDER
    control_panel_doc.site_path = SITE_PATH
    control_panel_doc.save()
    frappe.db.commit()


def prompt_for_input(prompt_message, default_value):
    """Used for prompting the cmd message for getting the inputs from the user"""
    if default_value:
        return default_value

    while True:
        user_input = input(prompt_message).strip()
        if user_input:
            return user_input


def get_required_fields():
    """Getting the inputs from the user then validate and trim the inputs"""
    _PROJECT_FOLDER = prompt_for_input(
        "Please enter the project name (i.e., DrAgarwals, EyeFoundation): ",
        PROJECT_FOLDER,
    )

    _SITE_PATH = prompt_for_input(
        "Please enter the site name (i.e., /home/bench/sites/site-name): ", SITE_PATH
    )

    if not SUB_DIR:
        frappe.throw("Please specify the sub directory in control panel:")

    HOME_PATH = construct_file_url("Home", _PROJECT_FOLDER)
    return _PROJECT_FOLDER, _SITE_PATH, HOME_PATH


def create_dir(dir, check=True):
    """Used os.makedirs for creating immediate directory"""
    os.makedirs(dir, exist_ok=check)


def create_project_folders():
    """Create the necessary folder structure for a project."""

    print("**------ Folder Structure Creating --------**")

    try:
        PROJECT_FOLDER, SITE_PATH, HOME_PATH = get_required_fields()
        if HOME_PATH not in get_file_doc_list({"is_folder": 1}):
            create_new_folder(PROJECT_FOLDER, "Home")

        for sub_item in SUB_DIR:
            sub_item_path = construct_file_url(HOME_PATH, sub_item)
            if sub_item_path not in get_file_doc_list({"is_folder": 1}):
                create_new_folder(sub_item, HOME_PATH)

            create_dir(construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, sub_item))
            
            for inner_folder_item in INNER_SUB_DIR:
                create_new_folder(inner_folder_item, sub_item_path)
                create_dir(construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, sub_item, inner_folder_item))

        print("**-------- Folder Structure Created --------**")
        
        set_control_panel(PROJECT_FOLDER, SITE_PATH)
        
    except Exception as e:
        frappe.throw(f"Error: {e}")


