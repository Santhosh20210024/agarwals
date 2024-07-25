import frappe
import hashlib
import unicodedata
import re
 
class UTRKeyCreator:
    def __init__(self, utr_number, doctype, name):
        self.utr_number = utr_number
        self.doctype = doctype
        self.name = name
        self.pattern = re.compile(r'[^a-zA-Z0-9]+')
 
    def format_utr(self, utr):
        variants = [
            utr,
            re.sub(self.pattern, '', utr),
            re.sub(r'.*uiic_', 'citin', utr),
            re.sub(r'.*uic_', 'citin', utr),
            re.sub(r'x+', '', utr),
            re.sub(r'^0+', '', utr)
        ]
       
        if utr.startswith(('23','24','25','26','27','28','29','30')) and len(utr) == 11:
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
        else:
            variants.extend(self.format_utr(utr))
 
        if utr.startswith('neft') and '-' in utr:
            variants.extend(self.format_utr(utr.split('-')[1]))
 
        elif utr.startswith('rtgs') and '-' in utr:
            variants.extend(self.format_utr(utr.split('-')[1]))
        variants = [variant for variant in variants if (variant.isnumeric() or variant.isalnum()) and len(variant) > 4 ]
        return set(variants)
 
    def process(self, utr_variants=None):
        key = hashlib.sha1(self.utr_number.encode('utf-8')).hexdigest()
       
        if utr_variants is None:
            utr_variants = list(self.get_variants())
           
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
 
    # def remove_x_in_UTR(self, utr):
    #     if "xxxxxxx" in utr:
    #         return utr.replace("xxxxxxx", '')
    #     elif "xx" in utr and len(utr) > 16:
    #         return utr.replace("xx", '')
    #     return utr
 