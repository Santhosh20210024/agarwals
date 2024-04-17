import frappe
import os
from frappe.model.document import Document
import shutil
from agarwals.utils.file_util import construct_file_url, HOME_PATH, SHELL_PATH, SUB_DIR, SITE_PATH, PROJECT_FOLDER
import zipfile

# Need to fix the auto increment serial number
class Fileupload(Document):
	def add_log_error(self, doctype, error):
		error_log = frappe.new_doc('Error Record Log')
		error_log.set('reference_doctype',doctype)
		error_log.set('error',error)
		error_log.save()

	def get_file_doc_meta(self):  # still unambiogues
		file_name = self.upload.split("/")[-1]
		file_doc_id = frappe.get_list("File", filters={'file_url': self.upload}, pluck='name')
		if len(file_doc_id) < 1:
			frappe.throw("Again upload the file.")
			return None, None
		else:
			return file_name, file_doc_id
	
	def delete_backend_files(self, file_path):  #unittested
		if os.path.exists(file_path):
			os.remove(file_path)

	def validate_hash_content(self, file_name, file_id):
		file_doc = frappe.get_doc('File', file_id)
		file_ch = file_doc.content_hash
		
		# verify the same hash content 
		if file_ch:
			file_doc_hash = frappe.get_list("File", filters = { 'content_hash':file_ch, 'attached_to_doctype': 'File upload' }, fields = [ 'name', 'attached_to_name' ], order_by = 'creation DESC')
			file_doc_hash_filtered = []

			for file in file_doc_hash:
				if frappe.get_value('File upload', file.attached_to_name, 'status') != 'Error': # Need to evaluate the error cases
					file_doc_hash_filtered.append(file) 
			
			if len(file_doc_hash_filtered) > 1:
				frappe.db.sql('DELETE FROM tabFile WHERE name = %(name)s', values={'name': file_doc_hash[0]['name']})
				frappe.db.commit()

				self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
				self.set(str(self.upload), None)
				frappe.throw('Duplicate File Error: The file being uploaded already exists. Please check.')
				return
			else:
				return

	def validate_file_check(self, file_id, file_name, file_extensions): #need to check
		frappe.delete_doc("File", file_id)
		frappe.db.sql('DELETE FROM tabFile WHERE name = %(name)s', values={'name':file_id})
		frappe.db.commit()

		self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
		self.set(str(self.upload), None)
		frappe.throw("Please upload files in the following format: " + ','.join(file_extensions))
 
	def validate_file(self): # check 1
		file_name, file_id = self.get_file_doc_meta()
		
		if file_id:
			try:
				file_extensions = frappe.get_single('Control Panel').allowed_file_extensions.split(',')
				file_parts = file_name.split('.')
				extension = file_parts[-1].upper()
				if extension not in file_extensions:
					self.validate_file_check(file_id, file_name, file_extensions)
					
			except Exception as e:
				self.add_log_error('File upload', str(e))
				self.validate_file_check(file_id, file_name, file_extensions) # check 1 -1
												
			self.validate_hash_content(file_name, file_id) # check 2
				
	def move_shell_file(self, source, destination, file_name, file_id):
		try:
			current_timestamp = str(frappe.utils.now()).split('.')[0]
			timestamped_file_name = current_timestamp.replace(' ', '-').replace(':','-') + '_' + file_name
			changed_source_file_name = source.replace( file_name, timestamped_file_name )

			os.rename(source, changed_source_file_name)
			shutil.move(changed_source_file_name, destination)

			return timestamped_file_name

		except Exception as e:
			err = frappe.new_doc('Error Record Log')
			err.doctype_name = 'File Upload'
			err.error_message = e
			err.save()
			frappe.db.sql('DELETE FROM tabFile WHERE name = %(name)s', values={'name':file_id})
			frappe.db.commit()
			self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, file_name))
			frappe.throw('Error:' + str(e))
			return

	def process_file_attachment(self):
     
		file_name, file_doc_id = self.get_file_doc_meta()
		file_doc = frappe.get_doc("File", file_doc_id)
		file_doc.folder = construct_file_url(HOME_PATH, SUB_DIR[0])
		if self.file_format == 'ZIP': 
			# There is a sperate folder for zip
			timestamped_file_name = self.move_shell_file(construct_file_url(SITE_PATH, SHELL_PATH, file_name),
										  construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[-1]),
										  file_name, file_doc_id)
		else:
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
		
	def update_zip_status(self): #unitested
		if self.file_format == 'ZIP':
			self.status = 'Zip'

	def count_zfiles(self, zip_list):
		file_count = 0
		for item in zip_list:
			if not item.endswith('/'):
				file_count += 1
		frappe.db.sql("""UPDATE `tabFile upload` set total_count = %(count)s where name = %(id)s""", values = {'count': file_count, 'id': self.name})
				
	def unzip_files(self):
		if os.path.exists(self.file):
			with zipfile.ZipFile(self.file) as zip_ref:
				zip_contents = zip_ref.namelist()
				self.set_count_zfiles(zip_contents)
				zip_ref.extractall()
				return zip_contents
		else:
			frappe.throw("Zip file is not found on the desired location")
			return False

	def validate(self): #unittested

		# To avoid other valid entries
		if self.status != 'Open':
			return
		
		if self.upload == None or self.upload == '':
			frappe.throw('Please upload file')

		self.validate_file()
		self.process_file_attachment()

		if self.file_format == 'ZIP':
			self.update_zip_status()

	def on_trash(self): #unittested
		self.delete_backend_files(construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0] , self.upload.split("/")[-1]))

	def save_file_manager(file_name, content):
		file_doc = frappe.get_doc(
			{
			"doctype": "File",
			"file_name": file_name, 
			"attached_to_doctype": None,
			"attached_to_name": None,
			"content": content,  
			"folder": "Home",
			"is_private": 1
		}
		)
		file_doc.save()
		frappe.db.commit()
		return file_doc.name
	
	def create_file_uploads(self, file_path):

		file_upload_doc = frappe.get_doc('File upload')
		file_upload_doc.file_format = 'EXCEL'
		if self.document_type == 'Debtors Report':
			file_upload_doc.document_type = 'Debtors Report'
		
		elif self.document_type == 'Claim Book':
			file_upload_doc.document_type = 'Claim Book'
		
		elif self.document_type == 'Settlement Advice':
			file_upload_doc.document_type = 'Settlement Advice'
			file_upload_doc.payer_type = self.payer_type
			self.validate_payer_name()

		elif self.document_type == 'Bank Transaction':
			file_upload_doc.document_type = 'Bank Transaction'
			self.validate_bank_transactions()
		file_upload_doc.upload = file_path
		file_upload_doc.save()

	def after_insert(self):
		if self.file_format == 'ZIP':
			try:
				files_list = self.unzip_files()
				if files_list:
					for file in files_list():
						if not file.endswith('/'):
							# shutil.move(construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0], file),  )
							with open(construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0], file), 'rb') as read_file:
								file_path = self.save_file_manager(read_file.content())
								# get the descending file
								# file_doc_hash = frappe.get_list("File", filters = { '': '' }, fields = [ 'name', 'attached_to_name' ], order_by = 'creation DESC')
								self.create_file_uploads(file_path)

			except Exception as e:
				pass