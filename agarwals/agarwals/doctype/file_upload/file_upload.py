import frappe
import os
from frappe.model.document import Document
from agarwals.utils.create_folders import SITE_PATH


class FileUpload(Document):

	def get_file_doc(self):
		file_name = str(self.upload).split("/")[-1]
		file_doc = frappe.get_list("File",filters={'file_name':file_name},pluck='name')
		return file_name, file_doc

	# validation based on types, upload
	def validate_fields(self):
		if self.type == None or self.type == "":
			frappe.throw("Select Type")
			return

		else:
			if self.type == "Bank Statement":
				if self.bank_account == None:
					frappe.throw("Select Bank Account")
				if self.upload == None:
					frappe.throw("Should Upload File")

			if self.type == "Debtor Statement":
				if self.debtor == None:
					frappe.throw("Select debtor")
				if self.upload == None:
					frappe.throw("Should Upload File")

			else:
				if self.upload == None or self.upload == '':
					frappe.throw("Should Upload File")
		

	def validate(self):
		self.validate_fields()
		self.validate_file()
		self.process_file_attachment()

	# Validate file extension and existence 
	def validate_file(self):

		file_name,file_doc = self.get_file_doc()

		# Allowed (.xlsx) only
		if file_doc and file_name.split(".")[-1].lower() != 'xlsx':
			# frappe.delete_doc("File",file_doc[0])
			# frappe.db.commit()
			frappe.throw("Upload excel file formats only")
		
		if file_doc and frappe.get_doc("File",file_doc[0]).folder != 'Home':
			frappe.throw("File is already present. The name should be unique. ")


	def check_valid_bank_file(self):
		pass


	# Process the file by type
	# Need to refactor
	def process_file_attachment(self):
		
		file_name,file_doc = self.get_file_doc()
		
		if file_doc:
			if self.type == "Bank Statement":
				
				# Doc Update Process
				dis_folder = "Home/DrAgarwals/Upload/Bank/" + self.bank_account
				bank_upload_path = frappe.get_doc("File",file_doc[0])
				bank_upload_path.folder = dis_folder
				bank_upload_path.file_url = "/private/files/DrAgarwals/Upload/Bank/" + self.bank_account + "/" + file_name

				self.upload = "/private/files/DrAgarwals/Upload/Bank/" + self.bank_account + "/" + file_name
				
				# local disk move option
				os.rename(SITE_PATH +  file_name, SITE_PATH  + "DrAgarwals/Upload/Bank/" + self.bank_account + "/" + file_name)
				
				bank_upload_path.save()

			if self.type == "Debtor Statement":
				
				dis_folder = "Home/DrAgarwals/Upload/Debtor_Payments/" + self.debtor
				debtor_upload_path = frappe.get_doc("File",file_doc[0])
				debtor_upload_path.folder = dis_folder
				debtor_upload_path.file_url = "/private/files/DrAgarwals/Upload/debtor_Payments/" + self.debtor + "/" + file_name

				self.upload = "/private/files/DrAgarwals/Upload/Debtor_Payments/" + self.debtor + "/" + file_name

				os.rename(SITE_PATH +  file_name, SITE_PATH  + "DrAgarwals/Upload/debtor_Payments/" + self.debtor + "/" + file_name)
				
				debtor_upload_path.save()

			if self.type == "Bill":

				dis_folder = "Home/DrAgarwals/Upload/Bills"
				bill_upload_path = frappe.get_doc("File",file_doc[0])
				bill_upload_path.folder = dis_folder
				bill_upload_path.file_url = "/private/files/DrAgarwals/Upload/Bills/" + file_name

				self.upload = "/private/files/DrAgarwals/Upload/Bills/" + file_name

				os.rename(SITE_PATH +  file_name, SITE_PATH  + "DrAgarwals/Upload/Bills/" + file_name)
				
				bill_upload_path.save()

			if self.type == "ClaimBook":

				dis_folder = "Home/DrAgarwals/Upload/Claimbook"
				claim_upload_path = frappe.get_doc("File",file_doc[0])
				claim_upload_path.folder = dis_folder
				claim_upload_path.file_url = "/private/files/DrAgarwals/Upload/Claimbook/" + file_name

				self.upload = "/private/files/DrAgarwals/Upload/Claimbook/" + file_name

				os.rename(SITE_PATH +  file_name, SITE_PATH  + "DrAgarwals/Upload/Claimbook/" + file_name)

				claim_upload_path.save()