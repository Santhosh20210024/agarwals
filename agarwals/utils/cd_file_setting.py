import pandas as pd
import frappe
import tempfile
import shutil
from agarwals.utils.path_data import SITE_PATH


@frappe.whitelist()
def file_folder_update():
    # Assuming you have your DataFrame in a variable named 'df'
    df = pd.DataFrame({'column1': [1, 2, 3], 'column2': ['A', 'B', 'C']})

    filename = "file_sample_test.xlsx"
    is_private = 1
    file_url = f"{SITE_PATH}/private/files/{filename}"
    folder = "Home/DrAgarwals/Transform"
    # Create a temporary XLSX file
    with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmpfile:
        excel_file_path = tmpfile.name
        df.to_excel(excel_file_path, index=False, engine='openpyxl')

        shutil.copy(excel_file_path, file_url)

        frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "folder": folder,
            "file_url": excel_file_path,
            "is_private": is_private
        }).insert()

    print(pd.read_excel(file_url).head())


