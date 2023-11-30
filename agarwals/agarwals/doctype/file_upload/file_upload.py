import frappe
import os
from frappe.model.document import Document
from agarwals.utils.importation_and_doc_creation import import_bank_statement
import shutil
from agarwals.utils.doc_meta_util import get_doc_fields
from agarwals.utils.file_util import construct_file_url
from agarwals.utils.path_data import HOME_PATH,SHELL_PATH,SUB_DIR,SITE_PATH,PROJECT_FOLDER

class FileUpload(Document):

	# passed
	def get_file_doc_data(self):
		file_name = str(self.get(self.uploaded_field)).split("/")[-1]
		file_doc_id = frappe.get_list("File", filters={'file_url':self.get(self.uploaded_field)},pluck='name')[0]
		return file_name, file_doc_id
	
	def get_uploaded_field(self):
		list_upload_fields = get_doc_fields("upload")
		upload_field_name = None
		
		for upload_field in list_upload_fields:
			# need to check
			if self.get( upload_field ) != None and self.get( upload_field ) != '':
				upload_field_name = upload_field
				break
		return upload_field_name
	
	def validate_hash_content(self,file_doc_id):
		file_doc = frappe.get_doc('File',file_doc_id)
		file_content_hash = file_doc.content_hash
		if file_content_hash:
			file_doc = frappe.get_list("File", filters={'content_hash':file_content_hash},pluck='name',order_by='creation DESC')
			if len(file_doc) > 1:
				frappe.delete_doc("File", file_doc[0])
				frappe.db.commit()
				self.upload = None
				frappe.throw('Duplicate File Error: The file being uploaded already exists. Please check.')
				return

	
	def validate_file(self):
		file_name, file_doc_id = self.get_file_doc_data()
		if file_doc_id:
			if file_doc_id != 'Home' and file_name.split(".")[-1].lower() != 'xlsx':
				frappe.delete_doc("File", file_doc_id)
				frappe.db.commit()
				frappe.throw("Please upload files in Excel format only (XLSX).")
				return
			self.validate_hash_content(file_doc_id)
				
	def move_shell_file(self, source, destination):
		try:
			if os.path.exists(source):
				os.rename(source, destination)
		except Exception as e:
			frappe.throw('Error:', str(e))
			return

	def process_file_attachment(self):
		file_name,file_doc_id = self.get_file_doc_data()
		_file_url = "/" + construct_file_url(SHELL_PATH,PROJECT_FOLDER,SUB_DIR[0],file_name)

		file_doc = frappe.get_doc("File", file_doc_id)
		file_doc.folder =   construct_file_url(HOME_PATH, SUB_DIR[0]) # NEED TO CHANGE
		file_doc.file_url = _file_url
		self.set(self.uploaded_field,_file_url) # need to change

		self.move_shell_file(construct_file_url(SITE_PATH,SHELL_PATH,file_name),construct_file_url(SITE_PATH,_file_url.lstrip('/') ))
		file_doc.save()

	def update_list_view(self):
		self.type = self.uploaded_field.replace("_upload", "")
		self.file_name = str(self.get(self.uploaded_field)).split("/")[-1]
		self.set(str(self.uploaded_field).replace('_upload','_uploaded'), self.file_name)
	    
	def validate(self):
		self.uploaded_field = self.get_uploaded_field()
		if not self.uploaded_field:
			frappe.throw('Please upload file')
			
        # need to refactor
		self.validate_file()
		self.process_file_attachment()
		self.update_list_view()
		
	def on_trash(self):
		print("----from on trash----")
		
	

# # # Copy_Files_Operation
# # def copy_files():
# # 	try:
# # 		file_upload_docs = frappe.get_list("File Upload",filters={'status':'Open'},fields=["upload","name"])
# # 		for every_file in file_upload_docs:
# # 		# Starting process
		
# # 			extract_file_name = frappe.get_list("File",filters={'file_url':every_file["upload"]},pluck="name")[0]
# # 			extract_file_doc = frappe.get_doc("File",extract_file_name)
			
# # 			transformed_file_doc = frappe.copy_doc(extract_file_doc)
# # 			transformed_file_url = transformed_file_doc.file_url.replace("Extract","Transform")
# # 			transformed_file_folder = transformed_file_doc.folder.replace("Extract","Transform")

# # 			extract_file_url_local = os.getcwd() + "/agarwals.com" + extract_file_doc.file_url
# # 			transformed_file_url_local = os.getcwd() + "/agarwals.com" + transformed_file_url

# # 			shutil.copy(extract_file_url_local,transformed_file_url_local)

# # 			transformed_file_doc.set("file_url",transformed_file_url)
# # 			transformed_file_doc.set("folder",transformed_file_folder)
# # 			transformed_file_doc.save()

# # 			file_doc = frappe.get_doc("File Upload",every_file["name"])
# # 			file_doc.status = "Transformed"
# # 			file_doc.transformed_file_url = transformed_file_doc.file_url
# # 			file_doc.save()

# # 		return "Success"
# # 	except:
# # 		return "Error in Transformation"


# # # For Custom Operation testing
# # @frappe.whitelist()
# # def bank_entry_operation():
# # 	return copy_files()
# # 	# Need to transform accordingly
# # for writing the clear option