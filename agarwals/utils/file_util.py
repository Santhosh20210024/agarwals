import frappe

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