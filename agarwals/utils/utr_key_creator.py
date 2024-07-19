import frappe
import hashlib
import unicodedata
import re

class UTRKeyCreator:
    def __init__(self, utr_number, doctype, name):
        self.utr_number = utr_number
        self.doctype = doctype
        self.name = name

    def get_variants(self):
        variants = []
        pattern = re.compile(r'[^a-zA-Z0-9]+')
        utr = unicodedata.normalize("NFKD", self.utr_number)
        utr = self.utr_number.lower().strip()
        variants.append(utr)
        variants.append(re.sub(pattern, '', utr))
        variants.append(re.sub(r'uiic_', 'citin', utr))
        variants.append(re.sub(r'uic_', 'citin', utr))
        variants.append(self.remove_x_in_UTR(utr))
        variants.append(re.sub(r'^0+', '', utr))
        
        if utr.startswith(('23','24','25','26','27','28','29','30')) and len(utr) == 11:
                variants.append("citin" + utr)
        
        if len(utr) == 9:
                variants.append('axiscn0' + utr)
           
        if utr.startswith("s") and len(utr) == 13:
            variants.append(utr[1:])
            
        if '/' in utr and len(utr.split('/')) == 2:
                extracted_utr = utr.split('/')[1]
                if '-' in extracted_utr:
                    variants.append(extracted_utr.split('-')[-1])
                else:
                    variants.append(self.remove_x_in_UTR(extracted_utr))
        if '-' in utr:
                variants.append(self.remove_x_in_UTR(utr.split('-')[-1]))
        else:
                variants.append(self.remove_x_in_UTR(utr))
                
        if utr.startswith('NEFT'):
            if '-' in utr:
                variants.append(self.remove_x_in_UTR(utr.split('-')[1]))
                
        elif utr.startswith('RTGS'):
            if '-' in utr:
                variants.append(self.remove_x_in_UTR(utr.split('-')[1]))
        
        return set(variants)

    def process(self, utr_variant = None):
        key = hashlib.sha1(self.utr_number.encode('utf-8')).hexdigest()
        if utr_variant == None:
            utr_variant_list = list(self.get_variants())
            
        for _utr in utr_variant_list:
            utr_key = frappe.new_doc('UTR Key')
            utr_key.set('utr_key', key)
            utr_key.set('utr_variant', _utr)
            utr_key.set('utr_number', self.utr_number)
            utr_key.set('reference_doctype', self.doctype)
            utr_key.set('reference_name', self.name)
            utr_key.save()
        frappe.db.commit()
        return [key]

    def remove_x_in_UTR(self, utr_number):
        if "xxxxxxx" in utr_number:
            return utr_number.replace("xxxxxxx", '')
        elif "xx" in utr_number and len(utr_number) > 16:
            return utr_number.replace("xx", '')
        return utr_number