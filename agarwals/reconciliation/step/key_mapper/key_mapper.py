import frappe
from agarwals.utils.error_handler import log_error

class KeyMapper:
    def __init__(self, records, doctype):
        self.records = records
        self.doctype = doctype
    
    def fetch_keys(self, key_id_variants, _type) -> list:
        if _type == 'UTR Key':
            return list(set(frappe.get_list("UTR Key", filters={'utr_variant': ['in', key_id_variants]}, pluck='utr_key')))
        elif _type == 'Claim Key':
            return list(set(frappe.get_list("UTR Key", filters={'utr_variant': ['in', key_id_variants]}, pluck='utr_key')))
        else:
            return list()
    
    def get_key_id_variants(self, KeyCreator, key_id, name):
        return list(eval(KeyCreator)(key_id, self.doctype, name).get_variants())
    
    def create_key(self, KeyCreator, key_id, name, variant):
        return eval(KeyCreator)(key_id, self.doctype, name).process(variant)
    
    def get_striped_key_id(self, key_id):
        return key_id.lower().strip()
    
    def map_keys(self, record):
        raise NotImplementedError("Subclasses should implement this method.")

    def process(self):
        try:
            for record in self.records:
                self.map_keys(record)
            frappe.db.commit()
        except (frappe.ValidationError, frappe.DatabaseError) as e:
            log_error(f"{e.__class__.__name__} in Key Processing: {str(e)}", doc=self.doctype)
            frappe.throw(f"Error while processing keys: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error in Key Processing: {str(e)}", doc=self.doctype)
            frappe.throw(f"Unexpected error while processing keys: {str(e)}")
    
    def update(self, query, key, name):
        frappe.db.sql(query, values={'name': name, 'key': key})
    
    def get_key_id_variants(self, KeyCreator, key_id, name):
        return list(eval(KeyCreator)(key_id, self.doctype, name).get_variants())
    
    def create_key(self, KeyCreator, key_id, name, variant):
        return eval(KeyCreator)(key_id, self.doctype, name).process(variant)
    
    def get_striped_key_id(self, key_id):
        return key_id.lower().strip()
    
    def map_keys(self, record):
        raise NotImplementedError("Subclasses should implement this method.")

    def process(self):
        try:
            for record in self.records:
                self.map_keys(record)
            frappe.db.commit()
        except (frappe.ValidationError, frappe.DatabaseError) as e:
            log_error(f"{e.__class__.__name__} in Key Processing: {str(e)}", doc=self.doctype)
            frappe.throw(f"Error while processing keys: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error in Key Processing: {str(e)}", doc=self.doctype)
            frappe.throw(f"Unexpected error while processing keys: {str(e)}")
    
    def update(self, query, key, name):
        frappe.db.sql(query, values={'name': name, 'key': key})