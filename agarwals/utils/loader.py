import frappe
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

    def change_status(self, doctype, name, status):
        frappe.db.set_value(doctype, name, 'status', status)

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
        frappe.db.set_value("Data Import",data_import.name,'name',file['name'])
        data_import.start_import()

    def process(self):
        files = self.get_files_to_load()
        if files == []:
            return None
        for file in files:
            self.change_status('Transform', file['name'], 'In Process')
            import_type = self.get_type_of_import(file)
            self.load_data(import_type,file)


