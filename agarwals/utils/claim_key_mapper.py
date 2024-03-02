import frappe
from agarwals.utils.claim_key_creator import ClaimKeyCreator

class ClaimKeyMapper:

    def get_record_obj(self, name):
        return None

    def get_claim_ids(self, record):
        return []

    def map_claim_keys(self, record):
        return None, None

    def create_claim_key(self, claim_id, doctype, name):
        return ClaimKeyCreator(claim_id, doctype, name).process()

    def process(self,records):
        for record in records:
            record_obj = self.get_record_obj(record)
            self.map_claim_keys(record_obj)
            record_obj.save()
        frappe.db.commit()


class BillClaimKeyMapper(ClaimKeyMapper):

    def get_record_obj(self, name):
        return frappe.get_doc('Bill', name)

    def get_doctype(self):
        return 'Bill'

    def map_claim_keys(self, record):
        doctype = self.get_doctype()
        
        if record.claim_id != '0' and record.claim_id is not None:
            if str(record.claim_id).strip() != '':
                claim_key = frappe.get_list("Claim Key", filters={'claim_variant': record.claim_id.lower().strip()}, pluck='claim_key')
                if not claim_key:
                    claim_key = self.create_claim_key(record.claim_id,doctype,record.name)
                record.set('claim_key', claim_key[0])

        if record.ma_claim_id:
            ma_claim_key = frappe.get_list("Claim Key", filters={'claim_variant': record.ma_claim_id.lower().strip()}, pluck='claim_key')

            if not ma_claim_key:
                ma_claim_key = self.create_claim_key(record.ma_claim_id, doctype, record.name)
            record.set('ma_claim_key', ma_claim_key[0])


class ClaimBookClaimKeyMapper(ClaimKeyMapper):

    def get_record_obj(self, name):
        return frappe.get_doc('ClaimBook', name)
    
    def get_doctype(self):
        return 'ClaimBook'

    def map_claim_keys(self, record):
        doctype = self.get_doctype()
        if record.al_number:
            claim_key = frappe.get_list("Claim Key", filters={'claim_variant': record.al_number.lower().strip()}, pluck='claim_key')
            if not claim_key:
                claim_key = self.create_claim_key(record.al_number,doctype,record.name)
            record.set('al_key', claim_key[0])
        if record.cl_number:
            claim_key = frappe.get_list("Claim Key", filters={'claim_variant': record.cl_number.lower().strip()}, pluck='claim_key')
            if not claim_key:
                claim_key = self.create_claim_key(record.cl_number,doctype,record.name)
            record.set('cl_key', claim_key[0])


class SAClaimKeyMapper(BillClaimKeyMapper):
    def get_doctype(self):
        return 'Settlement Advice'

    def get_record_obj(self, name):
        return frappe.get_doc('Settlement Advice', name)
    
    def map_claim_keys(self, record):
        doctype = self.get_doctype()
        
        claim_key = frappe.get_list("Claim Key", filters={'claim_variant': record.claim_id.lower().strip()}, pluck='claim_key')
        if not claim_key:
            claim_key = self.create_claim_key(record.claim_id,doctype,record.name)
    
        record.set('claim_key', claim_key[0])


@frappe.whitelist()
def map_claim_key():
    n = 1000
    bill_records = frappe.db.sql("""select name from tabBill where claim_key is NULL or ma_claim_key is NULL""", as_dict = True)
    bill_records = [i['name'] for i in bill_records]

    for i in range(0, len(bill_records), n):
        frappe.enqueue(BillClaimKeyMapper().process, job_name= "Claim Key Mapper in Bill", queue='long', is_async=True, timeout=18000, records = bill_records[i:i + n])
    
    claim_records = frappe.get_list("ClaimBook", filters={'al_key': '', 'cl_key': ''}, pluck='name')

    for i in range(0,len(claim_records),n):
        frappe.enqueue(ClaimBookClaimKeyMapper().process, job_name= "Claim Key Mapper in ClaimBook", queue='long', is_async=True, timeout=18000, records = claim_records[i:i + n])

    sa_records = frappe.get_list("Settlement Advice",
                    filters={'claim_key': '', 'claim_id': ['not in', ['', '00']]}, pluck='name')

    for i in range(0,len(sa_records),n):
        frappe.enqueue(SAClaimKeyMapper().process, job_name= "Claim Key Mapper in Settlement Advice", queue='long', is_async=True, timeout=18000, records = sa_records[i:i + n])


