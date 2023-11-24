import frappe
import os
from frappe.model.document import Document
from agarwals.utils.create_folders import SITE_PATH
from agarwals.utils.import_bank_statement import import_bank_statement
import shutil


class FileUpload(Document):

	def get_file_doc(self):
		file_name = str(self.upload).split("/")[-1]
		file_doc = frappe.get_list("File",filters={'file_name':file_name},pluck='name')
		return file_name, file_doc


	# validation based on types, Extract
	def validate_fields(self):
		if self.type == None or self.type == "":
			frappe.throw("Select Type")
			return

		else:
			if self.type == "Bank Statement":
				if self.bank_account == None:
					frappe.throw("Select Bank Account")
				if self.upload == None:
					frappe.throw("Should Extract File")

			if self.type == "Debtor Statement":
				if self.debtor == None:
					frappe.throw("Select debtor")
				if self.upload == None:
					frappe.throw("Should Upload File")

			else:
				if self.upload == None or self.upload == '':
					frappe.throw("Should Upload File")
		

	def validate(self):
		# self.status = "Open"
		self.validate_fields()
		self.validate_file()
		# if self.status
		if self.status == "Open":
			self.process_file_attachment()

	# Validate file extension and existence 
	def validate_file(self):

		file_name,file_doc = self.get_file_doc()

		# Allowed (.xlsx) only
		if file_doc and file_name.split(".")[-1].lower() != 'xlsx':
			# frappe.delete_doc("File",file_doc[0])
			# frappe.db.commit()
			frappe.throw("Upload excel file formats only")
		
		# if file_doc and frappe.get_doc("File",file_doc[0]).folder != 'Home':
		# 	frappe.throw("File is already present. The name should be unique. ")


	def check_valid_bank_file(self):
		pass


	# Process the file by type
	# Need to refactor
	def process_file_attachment(self):
		
		file_name,file_doc = self.get_file_doc()
		
		if file_doc:
			if self.type == "Bank Statement":
				
				# Doc Update Process
				dis_folder = "Home/DrAgarwals/Extract/Bank"
				bank_upload_path = frappe.get_doc("File",file_doc[0])
				bank_upload_path.folder = dis_folder
				bank_upload_path.file_url = "/private/files/DrAgarwals/Extract/Bank/" + file_name

				self.upload = "/private/files/DrAgarwals/Extract/Bank/" + file_name
				
				# local disk move option
				os.rename(SITE_PATH +  file_name, SITE_PATH  + "DrAgarwals/Extract/Bank/"  + file_name)
				
				bank_upload_path.save()

			if self.type == "Debtor Statement":
				
				dis_folder = "Home/DrAgarwals/Extract/Payment Advice"
				debtor_upload_path = frappe.get_doc("File",file_doc[0])
				debtor_upload_path.folder = dis_folder
				debtor_upload_path.file_url = "/private/files/DrAgarwals/Extract/Payment Advice/" + file_name

				self.upload = "/private/files/DrAgarwals/Extract/Payment Advice/"+ file_name

				os.rename(SITE_PATH +  file_name, SITE_PATH  + "DrAgarwals/Extract/Payment Advice/" + file_name)
				
				debtor_upload_path.save()

			if self.type == "Bill":

				dis_folder = "Home/DrAgarwals/Extract/Bill"
				bill_upload_path = frappe.get_doc("File",file_doc[0])
				bill_upload_path.folder = dis_folder
				bill_upload_path.file_url = "/private/files/DrAgarwals/Extract/Bill/" + file_name

				self.upload = "/private/files/DrAgarwals/Extract/Bill/" + file_name

				os.rename(SITE_PATH +  file_name, SITE_PATH  + "DrAgarwals/Extract/Bill/" + file_name)
				
				bill_upload_path.save()

			if self.type == "ClaimBook":

				dis_folder = "Home/DrAgarwals/Extract/Claimbook"
				claim_upload_path = frappe.get_doc("File",file_doc[0])
				claim_upload_path.folder = dis_folder
				claim_upload_path.file_url = "/private/files/DrAgarwals/Extract/Claimbook/" + file_name

				self.upload = "/private/files/DrAgarwals/Extract/Claimbook/" + file_name

				os.rename(SITE_PATH +  file_name, SITE_PATH  + "DrAgarwals/Extract/Claimbook/" + file_name)

				claim_upload_path.save()


# Copy_Files_Operation
def copy_files():
	try:
		file_upload_docs = frappe.get_list("File Upload",filters={'status':'Open'},fields=["upload","name"])
		for every_file in file_upload_docs:
		# Starting process
		
			extract_file_name = frappe.get_list("File",filters={'file_url':every_file["upload"]},pluck="name")[0]
			extract_file_doc = frappe.get_doc("File",extract_file_name)
			
			transformed_file_doc = frappe.copy_doc(extract_file_doc)
			transformed_file_url = transformed_file_doc.file_url.replace("Extract","Transform")
			transformed_file_folder = transformed_file_doc.folder.replace("Extract","Transform")

			extract_file_url_local = os.getcwd() + "/agarwals.com" + extract_file_doc.file_url
			transformed_file_url_local = os.getcwd() + "/agarwals.com" + transformed_file_url

			shutil.copy(extract_file_url_local,transformed_file_url_local)

			transformed_file_doc.set("file_url",transformed_file_url)
			transformed_file_doc.set("folder",transformed_file_folder)
			transformed_file_doc.save()

			file_doc = frappe.get_doc("File Upload",every_file["name"])
			file_doc.status = "Transformed"
			file_doc.transformed_file_url = transformed_file_doc.file_url
			file_doc.save()

		return "Success"
	except:
		return "Error in Transformation"


# For Custom Operation testing
@frappe.whitelist()
def bank_entry_operation():
	return copy_files()
	# Need to transform accordingly

@frappe.whitelist()
def loading():
	transformed_files = frappe.get_list('File Upload',filters={'status':'Transformed'},fields=['bank','bank_account','transformed_file_url','name'])
	for every_file in transformed_files:
		bank = every_file.bank
		bank_account = every_file.bank_account
		transformed_file_url = every_file.transformed_file_url
		import_bank_statement(bank = bank,bank_account = bank_account,attached_file= transformed_file_url)

		file_doc = frappe.get_doc("File Upload",every_file["name"])
		file_doc.status = "Loaded"
		file_doc.save()
	return "Success"
	


	