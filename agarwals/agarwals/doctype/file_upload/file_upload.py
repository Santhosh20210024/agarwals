import frappe
import shutil
import zipfile
import magic
import os
import openpyxl
from frappe.model.document import Document
from agarwals.utils.file_util import construct_file_url, HOME_PATH, SHELL_PATH, SUB_DIR, SITE_PATH, PROJECT_FOLDER

class Fileupload(Document):
	""" Fileupload is the custom class mainly created for handling the agarwals files"""

	extract_folder = construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0]) 
	zip_folder = construct_file_url(SITE_PATH, SHELL_PATH, PROJECT_FOLDER, SUB_DIR[-1]) 

	def add_log_error(self, doctype, error):  # To add error log 
		error_log = frappe.new_doc('Error Record Log')
		error_log.set('reference_doctype', doctype)
		error_log.set('error', error)
		error_log.save()

	def get_fpath_fdir(self): # Used while Zip Processing
		fname = self.upload.split('/')[-1]
		fpath = "".join([self.zip_folder ,'/', fname])
		fdir = "".join([self.zip_folder, '/', fname.split('.')[0]])
		return fpath, fdir
	
	def get_fdoc_meta(self): # To get the info of the file uploaded initially 
		fname = self.upload.split("/")[-1]
		fdoc_id = frappe.get_list("File"
								  ,filters={'file_url': self.upload}
								  ,pluck='name')
		if len(fdoc_id) < 1:
			frappe.throw("Should upload the file again.")
			return None, None
		else:
			return fname, fdoc_id
	
	def get_fdate_format(self, fname):   # To add the timestamped name while uploading
		curr_timestamp = str(frappe.utils.now()).split('.')[0]
		return curr_timestamp.replace(' ', '-').replace(':','-') + '_' + fname
	
	def del_file_record(self, fid, fname, err): # For deleting frappe file doctype record 
		self.del_private_file(construct_file_url(SITE_PATH, SHELL_PATH, fname))
		frappe.delete_doc("File", fid)
		frappe.db.commit()
		
		if err:
			frappe.throw(err)
	
	def del_private_file(self, fpath): # For deleting the private files. 
		if os.path.exists(fpath):
			os.remove(fpath)

	def update_zip_status(self):
		""" Update the file upload status as zip to avoid conflict while processing other files"""
		if self.file_format == 'ZIP':
			self.status = 'Zip'

	def validate_file_hash(self, fname, fid):  # Need to evaluate the frappe hashing concept
		""" Verify Hash Content 
			( based on frappe's in-build content-hash )
			args: file_name, file_id
			return nothing
		"""
		fdoc = frappe.get_doc('File', fid)
		fhash = fdoc.content_hash
		
		if fhash:
			filtered_corres_fdoc = []
			corres_fdoc = frappe.get_list("File", 
								   			filters = { 'content_hash': fhash, 'attached_to_doctype': 'File upload' }, 
								   			fields = [ 'name', 'attached_to_name' ],
								   			order_by = 'creation DESC')

			"""For avoiding the files hash validation"""
			for file in corres_fdoc:
				if frappe.get_value('File upload', file.attached_to_name, 'status') != 'Error':
					filtered_corres_fdoc.append(file) 
			
			if len(filtered_corres_fdoc) > 1:
				fid = corres_fdoc[0]['name']
				err = 'Duplicate File Error: The file being uploaded already exists. Please check.'
				self.del_file_record(fid, fname, err)

	
	def is_valid_excel_file(self, fname, fid):
		if os.path.exists(construct_file_url(SITE_PATH, SHELL_PATH, fname)):
			mime = magic.Magic(mime=True)
			file_mime = mime.from_file(construct_file_url(SITE_PATH, SHELL_PATH, fname))
			print(file_mime)
			if file_mime not in [
			'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # XLSX
			'application/vnd.ms-excel',                                           # XLS
			'text/csv',                                                           # CSV
			'application/vnd.ms-excel.sheet.binary.macroenabled.12',              # XLSB
			]:
				err = "Excel File is Invalid!"
				self.del_file_record(fid, fname, err)

	def is_valid_zip_file(self, fname, fid):
		if os.path.exists(construct_file_url(SITE_PATH, SHELL_PATH, fname)):
			mime = magic.Magic(mime=True)
			file_mime = mime.from_file(construct_file_url(SITE_PATH, SHELL_PATH, fname))
			if file_mime not in [
			 'application/zip'    												# ZIP
			]:
				err = "Zip File is Invalid!"
				self.del_file_record(fid, fname, err)
	
	def validate_file_format(self, fname, fid):
		file_extensions = frappe.get_single('Control Panel').allowed_file_extensions.split(',')
		extension = fname.split('.')[-1].upper().strip()

		if extension not in file_extensions: # Extention Checking
			err = f"Please upload files in the following format: {','.join(file_extensions)}"
			self.del_file_record(fid, fname, err)

		if self.file_format == 'EXCEL':
			if extension in ['XLSX','XLS','CSV','XLSB']:
				self.is_valid_excel_file(fname, fid)
			else:
				err = f"EXCEL Format: Should upload files such as ('XLSX', 'XLS','CSV','XLSB')"
				self.del_file_record(fid, fname, err)

		if self.file_format == 'ZIP':
			if extension == self.file_format:
				self.is_valid_zip_file(fname, fid)
				# self.is_duplicate_file(fname, fid)
			else:
				err = f"ZIP Format: Should upload zip file only"
				self.del_file_record(fid, fname, err)

	def validate_file(self): 
		fname, fid = self.get_fdoc_meta()
		
		if fid:
			self.validate_file_format(fname, fid) 
			self.validate_file_hash(fname, fid)

	def update_fdoc_upload(self, fid, furl, fname): 
		"After moving and added timestamp, update the corresponding file upload doc's fields"
		try:
			self.set("upload", furl)
			self.set("file", fname)
		except Exception as e:
			self.add_log_error('File upload', str(e))
			self.del_file_record(fid, fname, str(e))
			return

	def move_and_rename_file(self, source, destination, fname, fid):
		"""
		function: move_and_rename_file
		args: 1. source:	Frappe default file upload path ( sitename/private/files/ folder )
			  2. destination: 	if file_format == 'Excel' -> move to: DrAgarwals/Extract/ folder 
			  					or if file_format == 'Zip' -> move to: DrAgarwals/Zip/ folder  
			  3. fname: file name
			  4. fid: file record id
		return: timestamp_fname

		'This funtion is created for moving the frappe default file upload path (files) to DrAgarwals Extract or Zip folders 
		and renaming the file name with current timestamp for avoiding conflicts while uploading other files'
		"""
		try:
			timestamp_fname = None
			if self.source != None:
				timestamp_fname = fname
			else:
				timestamp_fname = self.get_fdate_format(fname)

			# Altered_fname mainly created for using in the shutil.move and os.rename functions
			altered_fname = source.replace(fname, timestamp_fname)
			os.rename(source, altered_fname)
			shutil.move(altered_fname, destination)
			return timestamp_fname

		except Exception as e:
			self.add_log_error('File upload', str(e))
			err = f'Error: {str(e)}'
			self.del_file_record(fid, fname, err)
			return
		
	def process_file_attachment(self):
		"""function: process_file_attachment
		   args: None
		   return: None
		   
		   For moving files from one path to another and update the fields based on it.
		"""
		fname, fid = self.get_fdoc_meta()
		fdoc = frappe.get_doc("File", fid)
		source = construct_file_url(SITE_PATH, SHELL_PATH, fname)
		timestamp_fname = None

		# Storing the zip files into another folder ( named as: zip )
		if self.file_format == 'ZIP':
			fdoc.folder = construct_file_url(HOME_PATH, SUB_DIR[-1])
			timestamp_fname = self.move_and_rename_file(source, self.zip_folder, fname, fid)
			fdoc.file_url = "/" + construct_file_url(SHELL_PATH, PROJECT_FOLDER, SUB_DIR[-1], timestamp_fname)

		else:
			fdoc.folder = construct_file_url(HOME_PATH, SUB_DIR[0])
			timestamp_fname = self.move_and_rename_file(source, self.extract_folder, fname, fid)
			fdoc.file_url = "/" + construct_file_url(SHELL_PATH, PROJECT_FOLDER, SUB_DIR[0], timestamp_fname)
		try:
			fdoc.save()
		except Exception as e:
			self.del_file_record(fid, fname, str(e))

		self.update_fdoc_upload(fid, fdoc.file_url, fname)
							
	def validate(self): 

		# To avoid the entire validation for non-open files		
		if self.status in ['In Process', 'Partial Success', 'Success', 'Error' ]:
			return

		if self.status == 'Zip' and self.zip_status in ['Open', 'Extracting', 'Extracted', 'Processed', 'Processing']:
			return
		
		if self.upload == None or self.upload == '':
			frappe.throw('Please upload file')

		self.validate_file()
		self.process_file_attachment()

		if self.file_format == 'ZIP':
			self.update_zip_status()

	def on_trash(self):
		if self.file_format == 'ZIP':
			fpath, fdir = self.get_fpath_fdir()
			self.del_private_file(fpath) 
			if os.path.exists(fdir):
				shutil.rmtree(fdir)
		else:
			self.del_private_file("".join([self.extract_folder, '/', self.upload.split("/")[-1]]))

	def save_file_record(self, fname, fcontent):
		frappe.get_doc(
			{
			"doctype": "File",
			"file_name": fname, 
			"attached_to_doctype": None,
			"attached_to_name": None,
			"content": bytes(fcontent),  
			"folder": "Home",
			"is_private": 1
		}
		).insert()

		frappe.db.commit()

	def upload_file_record(self, flist):
		fname, fdir = self.get_fpath_fdir()
		for file in flist:
			if not file.endswith('/'):
				with open(construct_file_url(fdir, file), 'rb') as read_file:
					self.save_file_record(file, read_file.read())
					self.del_private_file(construct_file_url(fdir, file))  
					# It will deleted the file in zip folder, once it moved to private/files/

	def create_child_entries(self, file, ffield): 
		mdoc = (frappe.new_doc('Settlement Advice Mapping') 
        if self.document_type == 'Settlement Advice' 
        else frappe.new_doc('Bank Account Mapping') 
        if self.document_type == 'Bank Statement' 
        else frappe.new_doc('Other Mapping'))

		mdoc.file_name = file
		mdoc.status = 'Open'
		mdoc.parenttype = 'File upload'
		mdoc.parent = self.name
		mdoc.parentfield = ( 'mapping_advice' if self.document_type == 'Settlement Advice'
					  		  else 'mapping_bank' if self.document_type == 'Bank Statement' 
							  else 'mapping_other')
		if ffield:
			if self.document_type == 'Settlement Advice':
				mdoc.payer_name = ffield
			if self.document_type == 'Bank Statement':
				mdoc.bank_account = ffield
				
		mdoc.save()
		frappe.db.commit()
		print('Created')
	
	def update_mapping_entries(self, flist, ffield = None): 
		try:
			for file in flist:
					self.create_child_entries(file, ffield)
			frappe.db.commit()	
		
		except Exception as e:
			self.add_log_error('File upload', str(e))

	def count_zipfiles(self, zip_list): 
		fcount = 0
		for zitem in zip_list:
			if not zitem.endswith('/'):
				fcount += 1
		return fcount

	def set_zipfiles_count(self, zip_list): 
		"""update zip file count"""
		fcount = self.count_zipfiles(zip_list)
		frappe.db.sql("""UPDATE `tabFile upload` set total_count = %(count)s where name = %(id)s"""
					  ,values = {'count': fcount, 'id': self.name})
		frappe.db.commit()
		
	def is_folder_exist(self, dir):
		if not os.path.exists(dir):
			os.mkdir(dir)

	def unzip_files(self):
		try:
			fpath, fdir = self.get_fpath_fdir()

			if os.path.exists(fpath):
				with zipfile.ZipFile(fpath) as _zip:
					zip_list = _zip.namelist()
					self.set_zipfiles_count(zip_list)
					self.is_folder_exist(fdir)
					_zip.extractall(fdir)
					return zip_list
			else:
				frappe.throw("The corresponding zip file is not found on the specified location")
				return False
			
		except Exception as e:
			self.add_log_error('File upload', str(e))
			frappe.throw('Error while processing the zip files')

	def load_files(self, ffield = None):
		if self.file_format == 'ZIP':
			try:
				flist = self.unzip_files()
				if flist:
					flist = [file for file in flist if not file.endswith('/')]
					self.update_mapping_entries(flist, ffield)
					self.upload_file_record(flist)

			except Exception as e:
				frappe.throw("Error!:"+ str(e))

# ----------------- RQ JOB : (Utils) -------------------
def extract_zip_files(fid, ffield = None):

	frappe.set_value('File upload', fid, 'zip_status', 'Extracting')

	fdoc = frappe.get_doc('File upload', fid)
	fdoc.load_files(ffield)
	frappe.db.commit()

	frappe.set_value('File upload', fid, 'zip_status', 'Extracted')


@frappe.whitelist()
def run_extractor(fid, ffield):
	fdoc = frappe.get_doc('File upload', fid)
	if fdoc.zip_status != 'Open' :
			frappe.throw('Already Extracted !')

	if not ffield.strip(): ffield = None
	# frappe.enqueue(extract_zip_files, job_name="ZipFileExtracting",  queue='long', is_async=True, timeout=18000, fid = fid, ffield = ffield)
	extract_zip_files(fid=fid,ffield=ffield)

def process_zip_entries(fid):

	def get_child_entries(cdoc, fid):
		return frappe.get_list(cdoc, filters={'parent': fid}, pluck = 'name')
	
	def set_child_entries_status(cdoc, status, fname = None, remark = None):
		frappe.set_value(cdoc, mfile, 'status', status)
		if fname: frappe.set_value(cdoc, mfile, 'file_id', fname)
		if remark: frappe.set_value(cdoc, mfile, 'remark', remark)

	fdoc = frappe.get_doc('File upload', fid)
	mlist = (get_child_entries('Settlement Advice Mapping', fid) 
			if fdoc.document_type == 'Settlement Advice'
			else get_child_entries('Bank Account Mapping', fid) 
			if fdoc.document_type == 'Bank Statement' 
			else get_child_entries('Other Mapping', fid))
	
	processed_count = 0
	for mfile in mlist:
		ndoc = frappe.new_doc('File upload')
		ndoc.file_format = 'EXCEL'
		ndoc.document_type = fdoc.document_type
		ndoc.source = fdoc.name

		if ndoc.document_type == 'Settlement Advice':
			ndoc.payer_type = frappe.get_value('Settlement Advice Mapping', mfile, 'payer_name')
			ndoc.upload =  "/" + construct_file_url(SHELL_PATH, frappe.get_value('Settlement Advice Mapping', mfile, 'file_name'))

		elif ndoc.document_type == 'Bank Statement':
			ndoc.bank_account = frappe.get_value('Bank Account Mapping', mfile, 'bank_account')
			ndoc.upload =  "/" + construct_file_url(SHELL_PATH, frappe.get_value('Bank Account Mapping', mfile, 'file_name'))
		
		else:
			ndoc.upload = "/" + construct_file_url(SHELL_PATH, frappe.get_value('Other Mapping', mfile, 'file_name'))

		try:
			ndoc.save()
			if ndoc.document_type == 'Settlement Advice': set_child_entries_status('Settlement Advice Mapping', 'Created', ndoc.name)
			elif ndoc.document_type == 'Bank Statement': set_child_entries_status('Bank Account Mapping', 'Created', ndoc.name)
			else: set_child_entries_status('Other Mapping', 'Created', ndoc.name)
		
			processed_count += 1
		except Exception as e:
			if ndoc.document_type == 'Settlement Advice': set_child_entries_status('Settlement Advice Mapping', 'Error', None, str(e))
			elif ndoc.document_type == 'Bank Statement': set_child_entries_status('Bank Account Mapping', 'Error', None, str(e))
			else: set_child_entries_status('Other Mapping', 'Error', None, str(e))

	frappe.set_value('File upload', fdoc.name, 'zip_status', 'Processed')
	frappe.set_value('File upload', fdoc.name, 'processed_count', processed_count)
	frappe.db.commit()

@frappe.whitelist()
def run_zip_entires(fid):
	fdoc = frappe.get_doc('File upload', fid)

	if fdoc.zip_status == 'Processed':
		frappe.throw('Already Processed !')
		return
	
	# Validation for avoiding the missing payer name and bank account while mapping
	if fdoc.document_type == 'Settlement Advice':
		if len(frappe.get_list('Settlement Advice Mapping', filters= {'parent': fid, 'payer_name':['=', '']})) > 0:
			frappe.throw("Please select payer for all the mapping records")

	if fdoc.document_type == 'Bank Statement':
		if len(frappe.get_list('Bank Account Mapping', filters= {'parent': fid, 'bank_account':['=', '']})) > 0:
			frappe.throw("Please select bank account for all the mapping records")
	# process_zip_entries()
	frappe.set_value('File upload', fid, 'zip_status', 'Processing')
	frappe.enqueue(process_zip_entries, job_name="ZipFileProcessing", queue='long', is_async=True, timeout=18000, fid = fid)