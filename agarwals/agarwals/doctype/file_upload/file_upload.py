import frappe
import os
from frappe.model.document import Document
import shutil
from agarwals.utils.doc_meta_util import get_doc_fields
from agarwals.utils.file_util import construct_file_url
from agarwals.utils.path_data import HOME_PATH, SHELL_PATH, SUB_DIR, SITE_PATH, PROJECT_FOLDER
import re

class Fileupload(Document):
	def get_file_doc_data(self):
		file_name = self.upload.split("/")[-1] # Need to the
		file_doc_id = frappe.get_list("File", filters={'file_url':self.upload}, pluck='name')
		if len(file_doc_id) < 1:
			frappe.throw("Again upload the file.")
			return None, None
		else:
			return file_name, file_doc_id
	
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
				frappe.db.sql('DELETE FROM tabFile WHERE name = %(name)s', values={'name': file_doc_hash[0]['name']})
				frappe.db.commit()

				# Delete the files
				self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
				self.set(str(self.upload), None)
				frappe.throw('Duplicate File Error: The file being uploaded already exists. Please check.')
				return
			else:
				return

	def validate_file_check(self, file_id, file_name, file_extensions):
		frappe.delete_doc("File", file_id)
		frappe.db.sql('DELETE FROM tabFile WHERE name in %(name)s', values={'name':file_id})
		frappe.db.commit()

		self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
		self.set(str(self.upload), None)
		frappe.throw("Please upload files in the following format: " + ','.join(file_extensions))

	def validate_file(self):
		file_name, file_id = self.get_file_doc_data()
		
		if file_id:
			try:
				file_extensions = frappe.get_single('Control Panel').allowed_file_extensions.split(',')
				if file_name.split('.')[-1].upper() not in file_extensions:
					self.validate_file_check(file_id, file_name, file_extensions)
					

			except Exception as e:
				self.validate_file_check(file_id, file_name, file_extensions)
												
			self.validate_hash_content(file_name, file_id)
				
	def move_shell_file(self, source, destination, file_name, file_id):
		try:
			current_timestamp = str(frappe.utils.now()).split('.')[0]
			timestamped_file_name = current_timestamp.replace(' ', '-') + '_' + file_name
			changed_source_file_name = source.replace( file_name, timestamped_file_name )

			# source name changed
			os.rename(source, changed_source_file_name)
			shutil.move(changed_source_file_name, destination)

			return timestamped_file_name

		except Exception as e:
			frappe.db.sql('DELETE FROM tabFile WHERE name = %(name)s', values={'name':file_id})
			frappe.db.commit()
			self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
			frappe.throw('Error:', str(e))
			return

	def process_file_attachment(self):
     
		file_name, file_doc_id = self.get_file_doc_data()
		file_doc = frappe.get_doc("File", file_doc_id)
		file_doc.folder = construct_file_url(HOME_PATH, SUB_DIR[0])
		timestamped_file_name = self.move_shell_file(construct_file_url(SITE_PATH, SHELL_PATH, file_name),
										  construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0]),
										  file_name, file_doc_id)

		file_doc.file_url = "/" + construct_file_url(SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0], timestamped_file_name)
		file_doc.save()

		self.set("upload", file_doc.file_url)
		self.set("file", file_name)

		if timestamped_file_name != None:
			self.set('file_name', timestamped_file_name)
			frappe.db.set_value('File', file_doc_id[0], 'file_name', timestamped_file_name)
			frappe.db.commit()
		
		
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
