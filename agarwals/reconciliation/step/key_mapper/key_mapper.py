import frappe
from agarwals.utils.error_handler import log_error
from tfs.orchestration import chunk


class KeyMapper:
    
    def __init__(self, records, record_type, key_type, chunk_doc):
        self.records = records
        self.record_type = record_type
        self.key_type = key_type
        self.chunk_doc = chunk_doc

    def fetch_keys(self, doctype, field, variants):
        key_field = field.replace('_variant', '_key')
        query = f"SELECT {key_field} FROM `tab{doctype}` WHERE {field} IN %s"
        results = frappe.db.sql(query, (variants,), as_list=True)
        return list(set(result[0] for result in results))

    def is_key_exist(self, key_id_variants, _tp) -> list:
        if not key_id_variants:
            return list()

        if _tp == "UTR Key":
            return self.fetch_keys("UTR Key", "utr_variant", key_id_variants)
        elif _tp == "Claim Key":
            return self.fetch_keys("Claim Key", "claim_variant", key_id_variants)
        else:
            return list()

    def get_keycreator_obj(self, KeyCreator, key_id, reference_name):
        KeyCreator = KeyCreator(key_id, self.key_type, reference_name, self.record_type)
        return KeyCreator

    @DeprecationWarning
    def get_key_id_variants(self, KeyCreator, key_id, reference_name):
        KeyCreator = KeyCreator(key_id, self.key_type, reference_name, self.record_type)
        return list(KeyCreator.get_variants())

    @DeprecationWarning
    def create_key(self, KeyCreator, key_id, reference_name, variant):
        return KeyCreator(
            key_id, self.key_type, reference_name, self.record_type
        ).process(variant)

    def get_striped_key_id(self, key_id):
        return key_id.lower().strip()

    def get_value(self, d, key, default):
        value = d.get(key, default)
        if value is None:
            return default
        return value

    def map_key(self, record):
        raise NotImplementedError("Subclasses should implement this method.")

    def process(self):
        try:
            for record in self.records:
                self.map_key(record)
            frappe.db.commit()
            chunk.update_status(self.chunk_doc, "Processed")
        except frappe.ValidationError as e:
            chunk.update_status(self.chunk_doc, "Error")
            log_error(
                f"Validation error in Key Processing: {str(e)}", doc=self.record_type
            )
            frappe.throw(f"Error while processing keys: {str(e)}")
        except Exception as e:
            chunk.update_status(self.chunk_doc, "Error")
            log_error(
                f"Unexpected error in Key Processing: {str(e)}", doc=self.record_type
            )
            frappe.throw(f"Unexpected error while processing keys: {str(e)}")

    def update(self, query, key, name):
        frappe.db.sql(query, values={"name": name, "key": key})
