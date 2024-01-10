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

	def validate_hash_content(self, file_name, file_id):
		file_doc = frappe.get_doc('File', file_id)
		file_ch = file_doc.content_hash
		
		# Verify the same hash content 
		if file_ch:
			file_doc_hash = frappe.get_list("File", filters = { 'content_hash':file_ch, 'attached_to_doctype': 'File upload' }, fields = [ 'name', 'attached_to_name' ], order_by = 'creation DESC')
			file_doc_hash_filtered = []

			for file in file_doc_hash:
				if frappe.get_value('File upload', file.attached_to_name, 'status') != 'Error':
					file_doc_hash_filtered.append(file) 
			
			if len(file_doc_hash_filtered) > 1:
				frappe.delete_doc("File", file_doc_hash[0])
				frappe.db.commit()

				# Delete the files
				self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
				self.set(str(self.upload), '')
				frappe.publish_realtime(event="Errorbox", message="error")
				self.set("upload",'')
				frappe.throw('Duplicate File Error: The file being uploaded already exists. Please check.')
				return 
			else:
				frappe.publish_realtime(event="Errorbox", message="no error")
				return
		

	def validate_file(self):
		file_name, file_id = self.get_file_doc_data()
		if file_id:
			file_extensions = frappe.get_single('Control Panel').allowed_file_extensions.split(',')
			if file_name.split('.')[-1].upper() not in file_extensions:
				frappe.delete_doc("File", file_id)
				frappe.db.commit()

				# Delete the shell files
				self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
				frappe.publish_realtime(event="Errorbox", message="error")
				frappe.throw("Please upload files in the following format: " + ','.join(file_extensions))
				self.set(str(self.upload), '')
				return
			
			else:
				frappe.publish_realtime(event="Errorbox", message="no error")									
			self.validate_hash_content(file_name, file_id)
				
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
		self.move_shell_file(construct_file_url(SITE_PATH, SHELL_PATH, file_name),construct_file_url(SITE_PATH, _file_url.lstrip('/') ))
		file_doc.save()
		self.set("upload",_file_url)
		self.set("upload_url",_file_url)
		
	def validate(self):

		# To avoid other valid entries
		if self.status != 'Open':
			return
		
		# To check whether the file uploaded
		if self.upload == None or self.upload == '':
			frappe.throw('Please upload file')

		self.validate_file()
		self.process_file_attachment()

	def on_trash(self):
		self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0] , self.upload.split("/")[-1]))
