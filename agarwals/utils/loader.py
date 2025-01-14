import shutil
import frappe
from frappe.core.doctype.data_import.data_import import start_import
from agarwals.utils.file_util import SITE_PATH
import os
from agarwals.utils.error_handler import log_error as error_handler

class Loader():
    def __init__(self,document_type):
        self.document_type = document_type

    def log_error(self, doctype_name, reference_name, error_message):
        error_handler(error=error_message, doc=doctype_name, doc_name=reference_name)

    def get_files_to_load(self):
        file_query = f"""SELECT 
                            name,file_url,type,parent
                        FROM 
                            `tabTransform` 
                        WHERE 
                            status = 'Open' AND document_type = '{self.document_type}' AND type != 'Skip'
                        ORDER BY 
                            creation"""
        files = frappe.db.sql(file_query, as_dict=True)
        return files

    def update_status(self, doctype, name, status):
        frappe.db.set_value(doctype, name, 'status', status)
        frappe.db.commit()

    def get_type_of_import(self,file):
        match file['type']:
            case 'Insert':
                return 'Insert New Records'

            case 'Update':
                return 'Update Existing Records'

    def load_data(self,import_type,file):
        try:
            data_import_mapping = frappe.get_doc("Data Import Mapping", self.document_type)
            template = data_import_mapping.template
        except Exception as e:
            template = 0
            self.log_error(self.document_type,file['name'],e)
        data_import = frappe.new_doc("Data Import")
        data_import.set('reference_doctype', self.document_type)
        data_import.set('import_type', import_type)
        data_import.set('import_file', file['file_url'])
        data_import.save()
        if template != 0:
            frappe.db.set_value("Data Import", data_import.name, 'template_options', template)
        start_import(data_import.name)
        frappe.db.commit()
        return data_import.name

    def get_import_status(self, import_name):
        import_doc = frappe.get_doc('Data Import',import_name)
        return import_doc.status

    def move_file(self,source_file,target_file):
        shutil.move(source_file,target_file)

    def update_file_url(self,file,target_file,import_name=None,status=None):
        if status == 'Error':
            file_doc = frappe.get_doc("File",{'attached_to_name':file['parent']})
            frappe.db.set_value("File", file_doc.name, {'file_url': target_file, 'folder': 'Home/DrAgarwals/Load/Error'})
        else:
            file_list_name = frappe.get_list('File', filters = {'file_url':file['file_url'],'attached_to_doctype':'Data Import','attached_to_name':import_name},pluck = 'name')[0]
            frappe.db.set_value("File", file_list_name, {'file_url':target_file,'folder':'Home/DrAgarwals/Load'})
            frappe.db.set_value("Data Import",import_name, 'import_file', target_file)
        frappe.db.set_value("Transform", file['name'], 'file_url', target_file)



    def delete_file_in_outside_folder(self, file_name,file):
        if file_name in os.listdir(SITE_PATH + '/private/files/'):
            try:
                os.remove(SITE_PATH + '/private/files/'+ file_name)
            except Exception as e:
                self.log_error('Transform', file['name'], e)

    def update_count(self, doctype, name, processed_count = 0, errored_count = 0):
        frappe.db.set_value(doctype, name, "processed_records", processed_count)
        frappe.db.set_value(doctype, name, "errored_records", errored_count)
        frappe.db.commit()

    def update(self, doctype, name, status, processed_count = 0, errored_count = 0):
        self.update_status(doctype, name, status)
        self.update_count(doctype, name, processed_count, errored_count)

    def process(self):
        files = self.get_files_to_load()
        if files == []:
            return None
        for file in files:
            file_name = file['file_url'].split("/")[-1]
            source_file = file['file_url']
            target_file = file['file_url'].replace('Transform', 'Load')
            try:
                self.update_status('Transform', file['name'], 'In Process')
                import_type = self.get_type_of_import(file)
                import_name = self.load_data(import_type, file)
                import_status = self.get_import_status(import_name)
                if import_status == 'Pending' or import_status == 'Error':
                    self.update('Transform', file['name'], 'Error', errored_count = frappe.get_doc('Data Import', import_name).payload_count)
                else:
                    processed, not_processed = frappe.db.count('Data Import Log', {'success': 1,
                                                                                   'data_import': import_name}), frappe.db.count(
                        'Data Import Log', {'success': 0, 'data_import': import_name})
                    self.update('Transform', file['name'], import_status, processed, not_processed)
                self.update_file_url(file, target_file, import_name)
                self.delete_file_in_outside_folder(file_name,file)
            except Exception as e:
                target_file = source_file.replace('/Transform/','/Load/Error/')
                self.update_file_url(file, target_file,status = 'Error')
                self.update_status('Transform', file['name'], 'Error')
                self.log_error('Transform', file['name'], e)
            self.move_file(SITE_PATH + source_file, SITE_PATH + target_file)





