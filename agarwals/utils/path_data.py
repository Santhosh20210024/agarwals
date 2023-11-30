import os
import frappe
PROJECT_FOLDER = "DrAgarwals"
HOME_PATH = "Home/DrAgarwals"
SHELL_PATH = "private/files"
SUB_DIR = ["Extract", "Tranform", "Load"]
INNER_SUB_DIR = ["Error"]
SITE_PATH = os.getcwd() + frappe.get_site_path()[1:]


