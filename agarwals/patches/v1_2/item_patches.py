import frappe
from agarwals.utils.error_handler import log_error
class ItemPathces:
    def create_item(self):
        try :
            item_record =  frappe.new_doc('Item')
            item_record.update({
                'item_code' : "Claim",
                'item_name' : "Claim",
                'item_group' : "Services"
            })
            item_record.save()
        except Exception as e :
            log_error(e, "Item")
            
    def create_tag(self):
        insert_records =[{'name':"Credit Payment"},{'name' : "Insurance"}]
        for record in insert_records :
            try:
                tag_record =  frappe.new_doc('Tag')
                tag_record.update({
                    'name': record.get('name')
                })
                tag_record.save()
            except Exception as e:
                log_error(e, "Tag")
            
            
    def create_document_naming_rule(self):
        try:
            document_record = frappe.new_doc('Document Naming Rule')
            document_record.update({
                'document_type' : "Bank Transaction",
                'prefix' : "X",
                'prefix_digits' : "7" 
            })
            document_record.save()
        except Exception as e :
            log_error(e, "Document Naming Rule")
                       
    def process (self):
        self.create_item()
        self.create_tag()
        self.create_document_naming_rule()
        

def execute():
    item_instance = ItemPathces()
    item_instance.process()