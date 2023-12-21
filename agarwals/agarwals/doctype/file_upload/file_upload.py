import frappe
import os
from frappe.model.document import Document
from agarwals.utils.importation_and_doc_creation import import_bank_statement
import shutil
from agarwals.utils.doc_meta_util import get_doc_fields
from agarwals.utils.file_util import construct_file_url
from agarwals.utils.path_data import HOME_PATH, SHELL_PATH, SUB_DIR, SITE_PATH, PROJECT_FOLDER
import re

class Fileupload(Document):
	# def __init__(self):
	# 	self.fil
	def get_file_doc_data(self):
		file_name = self.upload.split("/")[-1]
		file_doc_id = frappe.get_list("File", filters={'file_url':self.upload}, pluck='name')[0]
		return file_name, file_doc_id
	
	def get_uploaded_field(self):
		list_upload_fields = get_doc_fields("upload")
		upload_field_name = None
		
		for upload_field in list_upload_fields:
			if self.get( upload_field ) != None and self.get( upload_field ) != '':
				upload_field_name = upload_field
				break
		return upload_field_name
	
	def delete_backend_files(self, file_path):
		if os.path.exists(file_path):
			os.remove(file_path)

	def validate_hash_content(self, file_name, file_doc_id):
		file_doc = frappe.get_doc('File', file_doc_id)
		doc_file_name = file_doc.file_name
		file_content_hash = file_doc.content_hash
		
		# Verify the same hash content 
		if file_content_hash:
			file_hash_doc = frappe.get_list("File", filters = {'content_hash':file_content_hash}, pluck = 'name', order_by = 'creation DESC')
			if len(file_hash_doc) > 1:
				frappe.delete_doc("File", file_hash_doc[0])
				frappe.db.commit()
				
				# Delete the files
				self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
				self.set(str(self.upload), '')
				frappe.throw('Duplicate File Error: The file being uploaded already exists. Please check.')
				return
		
		# Verify the same file with different hash content
		file_name_list = frappe.get_list("File", filters = {'file_name': doc_file_name}, pluck = 'name', order_by = 'creation ASC')
		if len(file_name_list) > 1:
			frappe.delete_doc("File", file_name_list[0])
			frappe.db.commit()

			# Delete the shell files
			self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))

	def validate_file(self):
		file_name, file_doc_id = self.get_file_doc_data()
		file_type = frappe.get_value('File',file_doc_id,'file_type')
		if file_doc_id:
			if file_type != 'XLSX' and file_type != 'PDF':
				frappe.delete_doc("File", file_doc_id)
				frappe.db.commit()
				
				# Delete the shell files
				self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
				frappe.throw("Please upload files in Excel format only (XLSX).")
				return
			self.validate_hash_content(file_name, file_doc_id)
				
	def move_shell_file(self, source, destination):
		try:
			if os.path.exists(source):
				os.rename(source, destination)
		except Exception as e:
			frappe.throw('Error:', str(e))
			return

	def process_file_attachment(self):
     
		file_name,file_doc_id = self.get_file_doc_data()
		_file_url = "/" + construct_file_url(SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0], file_name)
		file_doc = frappe.get_doc("File", file_doc_id)
		file_doc.folder =   construct_file_url(HOME_PATH, SUB_DIR[0])
		file_doc.file_url = _file_url
		print("-------------------------  file url 1 -----------------------------------",_file_url)
		self.move_shell_file(construct_file_url(SITE_PATH, SHELL_PATH, file_name),construct_file_url(SITE_PATH, _file_url.lstrip('/') ))
		print("-------------------------  file url -----------------------------------",_file_url)
		file_doc.save()
		self.set("upload",_file_url)
		self.set("upload_url",_file_url)
		#self.set("upload_url", _file_url)
		
		

	# def update_list_view(self):
	# 	self.type = self.upload.replace("_upload", "")
	# 	self.file_name = str(self.get(self.upload)).split("/")[-1]
	# 	self.set(str(self.upload).replace('_upload', '_uploaded'), self.file_name)
	    
	def validate(self):
		# print("-----------",type(self.upload))
		
		if self.status != 'Open':
			return
		
		# print(len(self.upload))

		if self.upload == None or self.upload == '':
			frappe.throw('Please upload file')

		self.validate_file()
		self.process_file_attachment()
		# self.update_list_view()
		
	def on_trash(self):
		self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0] , self.upload.split("/")[-1]))