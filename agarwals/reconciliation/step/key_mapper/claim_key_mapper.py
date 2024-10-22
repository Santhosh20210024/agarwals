import frappe
from agarwals.reconciliation.step.key_mapper.key_mapper import KeyMapper
from agarwals.reconciliation.step.key_creator.claim_key_creator import ClaimKeyCreator
from agarwals.reconciliation.step.key_mapper.mapper_utils import enqueue_record_processing
from agarwals.utils.error_handler import log_error
from agarwals.utils.str_to_dict import cast_to_dic
from tfs.orchestration import ChunkOrchestrator


class ClaimKeyMapper(KeyMapper):
    """
    ClaimKeyMapper is used as base class for various UTR related doctypes
    Methods:
        insert_claim_keys: return None
        map_key : return None
    """
    def __init__(self, records, record_type, query):
        super().__init__(records, record_type, "Claim Key")
        self.query = query
    
    def insert_claim_keys(self, name, claim_key):
        """Used to insert into bill claim key and claimbook claim key"""
        doctype_mapping = {
            'Bill': ("Bill Claim Key", "bill"),
            'ClaimBook': ("ClaimBook Claim Key", "claimbook"),
            'Settlement Advice': ("Settlement Advice Claim Key", "settlement_advice"),
        }

        if self.record_type in doctype_mapping.keys():
            doctype, field_name = doctype_mapping[self.record_type]
            key_doc = frappe.new_doc(doctype)
            setattr(key_doc, field_name, name)
            key_doc.claim_key = claim_key	
            key_doc.save(ignore_permissions=True)		
            frappe.db.commit()

    def map_key(self, record):
        """ 
        Map Key is used to create a new key or to check whether there is any existing key for that variants,
        and update the corresponding values in respective doctypes.
        """
        try:
            _temp = {}
            for field in self.query.keys():
                key_id = self.get_refined_key_id(self.get_value(record, field, ''))
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
                        
                        if key[0] != 'IGNORED':
                            if self.record_type in ('Bill','ClaimBook','Settlement Advice'):
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
    def __init__(self, records):
        super().__init__(
            records,
            "Bill",
            {'claim_key_id': """UPDATE `tabBill` SET claim_key = %(key)s WHERE name = %(name)s""",
             'ma_key_id': """UPDATE `tabBill` SET ma_claim_key = %(key)s WHERE name = %(name)s"""}
        )

class ClaimBookClaimKeyMapper(ClaimKeyMapper):
    def __init__(self, records):
        super().__init__(
            records,
            "ClaimBook",
            {'al_key_id': """UPDATE `tabClaimBook` SET al_key = %(key)s WHERE name = %(name)s""",
             'cl_key_id': """UPDATE `tabClaimBook` SET cl_key = %(key)s WHERE name = %(name)s"""}
        )

class SettlementAdviceClaimKeyMapper(ClaimKeyMapper):
    def __init__(self, records):
        super().__init__(
            records,
            "Settlement Advice",
            {'claim_key_id':"""UPDATE `tabSettlement Advice` SET claim_key = %(key)s WHERE name = %(name)s""",
             'cl_key_id': """UPDATE `tabSettlement Advice` SET cl_key = %(key)s WHERE name = %(name)s"""}
        )
                                        
@frappe.whitelist()
def process(args={"type": "claim_key", "step_id": "", "queue": "long"}):
    args = cast_to_dic(args)

    mappers = {
        "Bill": BillClaimKeyMapper,
        "ClaimBook": ClaimBookClaimKeyMapper,
        "Settlement Advice": SettlementAdviceClaimKeyMapper
    }

    ChunkOrchestrator().process(enqueue_record_processing, 
                                step_id=args["step_id"],
                                type="ClaimKey",
                                mappers=mappers, 
                                args=args, 
                                job_name="ClaimKeyMapper")
