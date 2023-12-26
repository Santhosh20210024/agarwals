import shutil
import frappe
import os
import openpyxl
from agarwals.utils.path_data import SITE_PATH


def copy_files(type):
	try:
		file_upload_docs = frappe.get_list("File Upload",filters={ 'status':'Open','document_type':type }, fields="*")
		if file_upload_docs:
			for file_upload_item in file_upload_docs:
				# file_upload_item = frappe.get_doc()
				if file_upload_item.upload:
					file_doc = frappe.get_doc("File Upload",file_upload_item.name)
					file_doc.status = "In Process"

					extract_file_name = frappe.get_list("File",filters={'file_url':file_upload_item.upload},pluck="name")
					for file in extract_file_name:
						extract_file_doc = frappe.get_doc("File",file)
						
						transformed_file_doc = frappe.copy_doc(extract_file_doc)
						
						transformed_file_url = transformed_file_doc.file_url.replace("Extract","Transform")
						transformed_file_folder = transformed_file_doc.folder.replace("Extract","Transform")
						
						extract_file_url_local = SITE_PATH + extract_file_doc.file_url
						transformed_file_url_local = SITE_PATH + transformed_file_url
						shutil.copy(extract_file_url_local,transformed_file_url_local)
						
						transformed_file_doc.set("file_url",transformed_file_url)
						transformed_file_doc.set("folder",transformed_file_folder)
						transformed_file_doc.save()
						file_doc.save()
						modify_column_values(type, extract_file_url_local)
						
			return "Success"
	except Exception as e:
		return e
	
def modify_column_values(type, file_name):
	workbook = openpyxl.load_workbook(file_name)
	if type == "Debtors Report":
		sheet = workbook.active
		column_letter = 'Branch'
		for row in sheet[column_letter]:
			for cell in row:
				cell.value += ' - A'
		workbook.save(file_name)
	
@frappe.whitelist()
def transform(document_type):
	try:
		responce_status = copy_files(document_type)
		return "Success"
	except Exception as e:
		return e
