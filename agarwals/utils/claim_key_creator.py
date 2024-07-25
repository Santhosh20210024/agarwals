import frappe
import hashlib
import unicodedata
import re
class ClaimKeyCreator:
    def __init__(self,claim_id, doctype, name):
        self.claim_id = claim_id
        self.doctype = doctype
        self.name = name

    def get_variant_claim_numbers(self):
        claim_id = unicodedata.normalize("NFKD", self.claim_id)
        variant_claim_number = []
        claim_id = claim_id.strip()
        variant_claim_number.append(claim_id)
        possible_claim_id = re.sub(r'-?\((\d)\)$', '', claim_id).lower()
        variant_claim_number.append(possible_claim_id)
        formatted_claim_id = claim_id.lower().replace(' ', '').replace('.', '').replace('alnumber', '').replace(
            'number', '').replace(
            'alno', '').replace('al-', '').replace('ccn', '').replace('id:', '').replace('orderid:', '').replace(':',
                                                                                                                 '').replace(
            '(', '').replace(')', '')
        variant_claim_number.append(formatted_claim_id)
        possible_claim_id = re.sub(r'-(\d)(\d)?$', '', formatted_claim_id)
        variant_claim_number.append(possible_claim_id)
        possible_claim_id = re.sub(r'-(\d)(\d)?$', r'\1\2', formatted_claim_id)
        variant_claim_number.append(possible_claim_id)
        possible_claim_id = re.sub(r'_(\d)(\d)?$', '', formatted_claim_id)
        variant_claim_number.append(possible_claim_id)
        possible_claim_id = re.sub(r'_(\d)(\d)?$', r'\1\2', formatted_claim_id)
        variant_claim_number.append(possible_claim_id)
        return set(variant_claim_number)

    def process(self,claim_variants = None):
        key = hashlib.sha1(self.claim_id.encode('utf-8')).hexdigest()
        if not claim_variants :
            return [None]
            
        for claim_number in claim_variants:
            claim_key = frappe.new_doc('Claim Key')
            claim_key.set('claim_key',key)
            claim_key.set('claim_variant',claim_number)
            claim_key.set('claim_id',self.claim_id)
            claim_key.set('reference_doctype',self.doctype)
            claim_key.set('reference_name',self.name)
            claim_key.save()
        frappe.db.commit()
        return [key]
