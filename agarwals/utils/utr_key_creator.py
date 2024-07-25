import frappe
import hashlib
import unicodedata
import re
 
class UTRKeyCreator:
    def __init__(self, utr_number, doctype, name):
        self.utr_number = utr_number
        self.doctype = doctype
        self.name = name
        self.non_alphanumeric_pattern  = re.compile(r'[^a-zA-Z0-9]+')
        self.utr_format_pattern  = re.compile(r'^(neft|rtgs|nft|eft)-(.+?)-(.+)$')
        self.citin_pattern = re.compile(r'^(23|24|25|26|27|28|29|30)\d{9}$')
 
    def format_utr(self, utr):
        utr = re.sub(self.non_alphanumeric_pattern , '', utr)
        if utr.isalpha() or len(utr) < 4:
            return []
 
        variants = [
            utr,
            re.sub(r'.*uiic_', 'citin', utr),
            re.sub(r'.*uic_', 'citin', utr),
            re.sub(r'x+', '', utr),
            re.sub(r'^0+', '', utr)
        ]
 
        if self.citin_pattern.match(utr):
            variants.append("citin" + utr)
 
        if len(utr) == 9:
            variants.append('aiscn0' + utr)
 
        if utr.startswith("s") and len(utr) == 13:
            variants.append(utr[1:])
 
        return variants
 
    def get_variants(self):
        utr = unicodedata.normalize("NFKD", self.utr_number).lower().strip()
        variants = self.format_utr(utr)
 
        if '/' in utr and len(utr.split('/')) == 2:
            extracted_utr = utr.split('/')[1]
            if '-' in extracted_utr:
                variants.extend(self.format_utr(extracted_utr.split('-')[-1]))
            else:
                variants.extend(self.format_utr(extracted_utr))
 
        if '-' in utr:
            variants.extend(self.format_utr(utr.split('-')[-1]))
 
        match = self.utr_format_pattern.match(utr)
        if match:
            _, utr_number, _ = match.groups()
            print(utr_number)
            variants.extend(self.format_utr(utr_number))
 
        return set(variants)
    
    def process(self, utr_variants = None):
        key = hashlib.sha1(self.utr_number.encode('utf-8')).hexdigest()
        
        if not utr_variants:
            return ["Full String Value"]

        for variant in utr_variants:
            utr_key = frappe.new_doc('UTR Key')
            utr_key.update({
                'utr_key': key,
                'utr_variant': variant,
                'utr_number': self.utr_number,
                'reference_doctype': self.doctype,
                'reference_name': self.name
            })
            utr_key.save()
 
        frappe.db.commit()
        return [key]
