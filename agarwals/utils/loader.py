import shutil
import frappe
from frappe.core.doctype.data_import.data_import import start_import
from agarwals.utils.path_data import SITE_PATH
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
        data_import_mapping = frappe.get_doc("Data Import Mapping", self.document_type)
        template = data_import_mapping.template
        data_import = frappe.new_doc("Data Import")
        data_import.set('reference_doctype', self.document_type)
        data_import.set('import_type', import_type)
        data_import.set('import_file', file['file_url'])
        data_import.save()
        frappe.db.set_value("Data Import", data_import.name, 'template_options', template)
        start_import(data_import.name)
        return data_import.name

    def get_import_status(self, import_name):
        import_doc = frappe.get_doc('Data Import',import_name)
        return import_doc.status

    def move_file(self,source_file,target_file):
        shutil.copy(source_file,target_file)

    def update_file_url(self,file,target_file):
        file_list_name = frappe.get_list('File', filters = {'file_url':file['file_url'],'attached_to_doctype':'Data Import'},pluck = 'name')[0]
        frappe.db.set_value("File", file_list_name, {'file_url':target_file,'folder':'Home/DrAgarwals/Load'})
        frappe.db.set_value("Transform",file['name'],'file_url',target_file)
        frappe.db.commit()

    def process(self):
        files = self.get_files_to_load()
        if files == []:
            return None
        for file in files:
            self.update_status('Transform', file['name'], 'In Process')
            import_type = self.get_type_of_import(file)
            import_name = self.load_data(import_type,file)
            import_status = self.get_import_status(import_name)
            if import_status == 'Pending' or import_status == 'Error':
                self.update_status('Transform', file['name'], 'Error')
            else:
                self.update_status('Transform', file['name'], import_status)
            source_file = file['file_url']
            target_file = file['file_url'].replace('Transform','Load')
            self.move_file(SITE_PATH + source_file,SITE_PATH + target_file)
            self.update_file_url(file,target_file)



