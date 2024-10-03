from agarwals.utils.str_to_dict import cast_to_dic
from tfs.orchestration import ChunkOrchestrator, chunk
import os
import frappe
from agarwals.utils.error_handler import log_error
import shutil

@ChunkOrchestrator.update_chunk_status
def create_sa_folders():
    try:
        control_panel = frappe.get_doc('Control Panel')
        PROJECT_FOLDER = control_panel.get("project_folder", None)
        SITE_PATH = control_panel.get("site_path", None)
        SHELL_PATH = "private/files"
        path = os.path.join(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, "Settlement Advice")
        if os.path.exists(path):
            folder_names = set(
                frappe.db.sql(
                    "SELECT tpa FROM `tabTPA Login Credentials` WHERE is_enable = 1",
                    pluck="tpa",
                )
            )
            for name in folder_names:
                folder = path + "/" + name
                if not os.path.exists(folder):
                    os.mkdir(folder)
                else:
                    if len(os.listdir(folder)) > 0:
                        shutil.rmtree(folder)
                        os.mkdir(folder)
                        log_error(error=f"Folder already exists: {name},it has been deleted and recreated",status='INFO')
        else:
            raise FileNotFoundError(f"Folder does not exist: {path}")

        return "Processed"
    except Exception as e:
        log_error(error=e)
        return "Error"

@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        ChunkOrchestrator().process(create_sa_folders,step_id=args["step_id"],is_enqueueable=True,
                                    queue=args["queue"])
    except Exception as e:
        log_error(error=e,doc_name='SA Folder Creator')
