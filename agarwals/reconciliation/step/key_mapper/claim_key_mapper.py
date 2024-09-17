import frappe
from agarwals.reconciliation.step.key_mapper.key_mapper import KeyMapper
from agarwals.reconciliation.step.key_creator.claim_key_creator import ClaimKeyCreator
from agarwals.reconciliation.step.key_mapper.utils import process_records
from agarwals.utils.error_handler import log_error
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.reconciliation import chunk


class ClaimKeyMapper(KeyMapper):
    """ 
    ClaimKeyMapper is used as base class for various UTR related doctypes
    Methods:
        insert_claim_keys: return None
        map_key : return None
    """
    def __init__(self, records, record_type, query, chunk_doc):
        super().__init__(records, record_type, "Claim Key", chunk_doc)
        self.query = query
    
    def insert_claim_keys(self, name, claim_key):
        """Used to insert into bill claim key and claimbook claim key"""
        if self.record_type == 'Bill':
            doctype = "Bill Claim Key"
            key_doc = frappe.new_doc(doctype)
            key_doc.bill = name
        else:
            doctype = "ClaimBook Claim Key"
            key_doc = frappe.new_doc(doctype)
            key_doc.claimbook = name
        key_doc.claim_key = claim_key	
        key_doc.save()		
        frappe.db.commit()

    def map_key(self, record):
        """ 
        Map Key is used to create a new key or to check whether there is any existing key for that variants,
        and update the corresponding values in respective doctypes.
        """
        try:
            _temp = {}
            for field in self.query.keys():
                key_id = self.get_striped_key_id(self.get_value(record, field, ''))
                if key_id:
                    if key_id not in _temp.keys():
                        KeyCreator = self.get_keycreator_obj(
                            ClaimKeyCreator, key_id, record["name"]
                        )
                        key_id_variants = KeyCreator.get_variants()
                        key = self.is_key_exist(key_id_variants, "Claim Key")
                        if len(key) > 1:
                            log_error(
                                f"Multiple keys found: {str(key)}", "Claim Key", "Key Mapping"
                            )
                            return
                        if not key: key = KeyCreator.process(key_id_variants)
                        if self.record_type in ('Bill', 'ClaimBook'):
                            self.insert_claim_keys(record["name"], key[0])
                        self.update(self.query[field], key[0], record["name"])
                        _temp[key_id] = key
                    else:
                        self.update(self.query[field], _temp[key_id], record["name"])

        except KeyError as e:
            log_error(
                f"KeyError in map_key: {str(e)}",
                "Claim Key",
                self.record_type,
            )
            frappe.throw(f"KeyError while processing Claim keys: {str(e)}")

        except frappe.DoesNotExistError as e:
            log_error(
                f"DoesNotExistError in map_key: {str(e)}",
                "Claim Key",
                self.record_type,
            )
            frappe.throw(f"DoesNotExistError while processing Claim keys: {str(e)}")

        except frappe.ValidationError as e:
            log_error(
                f"ValidationError in map_key: {str(e)}",
                "Claim Key",
                self.record_type,
            )
            frappe.throw(f"ValidationError while processing Claim keys: {str(e)}")

        except Exception as e:
            log_error(
                f"Unexpected error in map_key: {str(e)}",
                "Claim Key",
                self.record_type,
            )
            frappe.throw(f"Unexpected error while processing Claim keys: {str(e)}")

class BillClaimKeyMapper(ClaimKeyMapper):
    def __init__(self, records, chunk_doc):
        super().__init__(
            records,
            "Bill",
            {'claim_key_id': """UPDATE `tabBill` SET claim_key = %(key)s WHERE name = %(name)s"""
            ,'ma_key_id': """UPDATE `tabBill` SET ma_claim_key = %(key)s WHERE name = %(name)s"""},
            chunk_doc
        )

class ClaimBookClaimKeyMapper(ClaimKeyMapper):
    def __init__(self, records, chunk_doc):
        super().__init__(
            records,
            "ClaimBook",
            {'al_key_id': """UPDATE `tabClaimBook` SET al_key = %(key)s WHERE name = %(name)s"""
            ,'cl_key_id': """UPDATE `tabClaimBook` SET cl_key = %(key)s WHERE name = %(name)s"""},
            chunk_doc
        )

class SettlementAdviceClaimKeyMapper(ClaimKeyMapper):
    def __init__(self, records, chunk_doc):
        super().__init__(
            records,
            "Settlement Advice",
            {'claim_key_id':"""UPDATE `tabSettlement Advice` SET claim_key = %(key)s WHERE name = %(name)s"""},
            chunk_doc
        )

query_mapper = {
                "Bill": """SELECT name, claim_id as claim_key_id, ma_claim_id as ma_key_id FROM tabBill 
                        WHERE ( claim_id != '0' AND claim_id != ' ' AND claim_id IS NOT NULL AND (claim_key is NULL or claim_key = '') ) 
                        or ( ma_claim_id != '0' AND ma_claim_id != ' ' AND ma_claim_id IS NOT NULL AND (ma_claim_key is NULL or ma_claim_key = '') )""",
                "ClaimBook": """SELECT name, al_number as al_key_id, cl_number as cl_key_id FROM `tabClaimBook` 
                                WHERE ( al_number != '0' AND al_number != ' ' AND al_number IS NOT NULL AND (al_key is NULL or cl_key = '') )
                                or ( cl_number != '0' AND cl_number != ' ' AND cl_number IS NOT NULL AND (cl_key is NULL or cl_key = '') ) """,
                "Settlement Advice": """SELECT name, claim_id as claim_key_id FROM `tabSettlement Advice` 
                                        WHERE claim_id != '0' AND claim_id != ' ' AND claim_id IS NOT NULL AND (claim_key is NULL or claim_key = '')"""
                }

@frappe.whitelist()
def process(args={"type":"claim_key", "step_id":"", "queue":"long"}): 
    try:
        args = cast_to_dic(args)
        chunk_size = int(args.get("chunk_size", 100))

        mappers = {
            "Bill": BillClaimKeyMapper,
            "ClaimBook": ClaimBookClaimKeyMapper,
            "Settlement Advice": SettlementAdviceClaimKeyMapper
        }

        for record_type, query in query_mapper.items():
            process_records(query, mappers[record_type], chunk_size, args)

    except Exception as e:
        log_error("Error While Processing: " + str(e), doc="Claim Key")