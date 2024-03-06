import shutil
import frappe
from frappe.core.doctype.data_import.data_import import start_import
from agarwals.utils.file_util import SITE_PATH
import os

class Loader():
    def __init__(self,document_type):
        self.document_type = document_type

    def log_error(self, doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()

    def get_files_to_load(self):
        file_query = f"""SELECT 
                            name,file_url,type
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

    def update_file_url(self,file,target_file,import_name):
        file_list_name = frappe.get_list('File', filters = {'file_url':file['file_url'],'attached_to_doctype':'Data Import','attached_to_name':import_name},pluck = 'name')[0]
        frappe.db.set_value("File", file_list_name, {'file_url':target_file,'folder':'Home/DrAgarwals/Load'})
        frappe.db.set_value("Transform",file['name'],'file_url',target_file)
        frappe.db.set_value("Data Import",import_name, 'import_file', target_file)

    def delete_file_in_outside_folder(self, file_name,file):
        if file_name in os.listdir(SITE_PATH + '/private/files/'):
            try:
                os.remove(SITE_PATH + '/private/files/'+ file_name)
            except Exception as e:
                self.log_error('Transform', file['name'], e)

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
                    self.update_status('Transform', file['name'], 'Error')
                else:
                    self.update_status('Transform', file['name'], import_status)
                self.update_file_url(file, target_file, import_name)
                self.delete_file_in_outside_folder(file_name,file)
            except Exception as e:
                self.update_status('Transform', file['name'], 'Error')
                self.log_error('Transform', file['name'], e)
            self.move_file(SITE_PATH + source_file, SITE_PATH + target_file)





