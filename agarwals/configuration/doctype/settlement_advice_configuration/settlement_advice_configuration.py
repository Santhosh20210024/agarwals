# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe
import pandas as pd
import os
import json
from frappe.model.document import Document

class SettlementAdviceConfiguration(Document):
	def validate(self):
		doc_val = frappe.get_all("File", {"file_name": self.file_name},['*'])
		validation_columns = self.get_config_file(self.columns_for_validation)
		if doc_val :
			if not self.check_columns():
				self.change_file(validation_columns)
		else:
			self.create_new_file(validation_columns)
		

	def get_config_file(self,columns_for_validation):
		sa_columns = columns_for_validation.replace("'", '"')
		columns = json.loads(sa_columns)
		return columns.get("Manual",[])
		

	def check_columns(self):
		previous_value = frappe.db.get_value("Settlement Advice Configuration",self.name,'columns_for_validation')
		if previous_value == self.columns_for_validation:
			return True
		return False


	def change_file(self,validation_columns):
		doc = frappe.get_doc("File",{'file_name':self.file_name})
		frappe.delete_doc('File',doc.name)   
		self.create_new_file(validation_columns)

	def create_new_file(self, validation_columns):

		validation_columns = [col for col in validation_columns if col]
		control_panel = frappe.get_single("Control Panel")
		home_path = "/private/files/"
		project_path = control_panel.project_folder
		directory_path = os.path.join(control_panel.site_path, home_path, project_path, "File Upload")
		os.makedirs(directory_path, exist_ok=True)
		if not self.file_name.endswith(('.csv','.xlsx')) :
			self.file_name += ".csv"
		site_path = os.path.join(directory_path, self.file_name)
		df = pd.DataFrame( columns=validation_columns)
		df.to_csv(site_path, index=False, header=True, columns=validation_columns)

		with open(site_path, 'rb') as f:
			file_data = f.read()

		new_file = frappe.get_doc({
			'doctype': 'File',
			'file_name': self.file_name,# Extract filename from the path
			'content': file_data,
			'is_private': 1  # Change to 1 for private files
		})
		new_file.save()
		frappe.db.commit()
