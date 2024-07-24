import frappe
from agarwals.utils.claim_key_creator import ClaimKeyCreator
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error

class ClaimKeyMapper:
    def get_record_obj(self, name):
        return None

    def get_claim_ids(self, record):
        return []

    def map_claim_keys(self, record):
        return None, None
    
    def get_variants(self, claim_id, doctype, name):
        return ClaimKeyCreator(claim_id, doctype, name).get_variant_claim_numbers()

    def create_claim_key(self, claim_id, doctype, name,claim_variant):
        return ClaimKeyCreator(claim_id, doctype, name).process(claim_variant)

    def process(self,records, chunk_doc):
        chunk.update_status(chunk_doc, "InProgress")
        try:
            for record in records:
                record_obj = self.get_record_obj(record)
                self.map_claim_keys(record_obj)
                record_obj.save()
            frappe.db.commit()
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")


class BillClaimKeyMapper(ClaimKeyMapper):
    def get_record_obj(self, name):
        return frappe.get_doc('Bill', name)
    def get_doctype(self):
        return 'Bill'

    def map_claim_keys(self, record):
        doctype = self.get_doctype()
        if record.claim_id != '0' and record.claim_id is not None:
            if str(record.claim_id).strip() != '':
                claim_variant = list(self.get_variants(record.claim_id, doctype, record.name))
                claim_key = list(set(frappe.get_list("Claim Key", filters={'claim_variant':['in',claim_variant]}, pluck='claim_key')))
                
                if len(claim_key) > 1:
                    log_error(str(claim_key),'Claim Key','Claim Key - Settlement Advice')
                    return
                
                if not claim_key:
                    claim_key = self.create_claim_key(record.claim_id,doctype,record.name,claim_variant)
                    insert_claim_keys(record.name,claim_key[0],'Bill Claim Key')
                record.set('claim_key', claim_key[0])
        if record.ma_claim_id:
            if record.ma_claim_id != '0' and record.ma_claim_id is not None:
                if str(record.ma_claim_id).strip() != '':
                    claim_variant = list(claim_variant = list(self.get_variants(record.ma_claim_id, doctype, record.name)))
                    ma_claim_key = list(set(frappe.get_list("Claim Key", filters={'claim_variant':['in',claim_variant]}, pluck='claim_key')))
                    if len(ma_claim_key) > 1:
                       log_error(str(ma_claim_key),'Claim Key','Claim Key - Settlement Advice')
                       return
                    if not ma_claim_key:
                        ma_claim_key = self.create_claim_key(record.ma_claim_id, doctype, record.name,claim_variant)
                        insert_claim_keys(record.name,claim_key[0],'Bill Claim Key')
                    record.set('ma_claim_key', ma_claim_key[0])

class ClaimBookClaimKeyMapper(ClaimKeyMapper):
    def get_record_obj(self, name):
        return frappe.get_doc('ClaimBook', name)
    
    def get_doctype(self):
        return 'ClaimBook'

    def map_claim_keys(self, record):
        doctype = self.get_doctype()
        if record.al_number != '0' and record.al_number is not None:
            if str(record.al_number).strip() != '':
                claim_variant = list(self.get_variants(record.al_number, doctype, record.name))
                claim_key = list(set(frappe.get_list("Claim Key", filters={'claim_variant':['in',claim_variant]}, pluck='claim_key')))
                
                if len(claim_key) > 1:
                    log_error(str(claim_key),'Claim Key','Claim Key - Settlement Advice')
                    return
                
                if not claim_key:
                    claim_key = self.create_claim_key(record.al_number,doctype,record.name,claim_variant)
                    insert_claim_keys(record.name,claim_key[0],'ClaimBook Claim Key')
                record.set('al_key', claim_key[0])
        if record.cl_number != '0' and record.cl_number is not None:
            if str(record.cl_number).strip() != '':
                
                claim_variant = list(self.get_variants(record.cl_number, doctype, record.name))
                claim_key = list(set(frappe.get_list("Claim Key", filters={'claim_variant':['in',claim_variant]}, pluck='claim_key')))
                
                if len(claim_key) > 1:
                    log_error(str(claim_key),'Claim Key','Claim Key - Settlement Advice')
                    return
                
                if not claim_key:
                    claim_key = self.create_claim_key(record.cl_number,doctype,record.name,claim_variant)
                    insert_claim_keys(record.name,claim_key[0],'ClaimBook Claim Key')
                record.set('cl_key', claim_key[0])

class SAClaimKeyMapper(BillClaimKeyMapper):
    def get_doctype(self):
        return 'Settlement Advice'

    def get_record_obj(self, name):
        return frappe.get_doc('Settlement Advice', name)

    def map_claim_keys(self, record):
        doctype = self.get_doctype()
        if record.claim_id != '0' and record.claim_id is not None:
            if str(record.claim_id).strip() != '':
                claim_variant = list(self.get_variants(record.claim_id, doctype, record.name))
                claim_key = list(set(frappe.get_list("Claim Key", filters={'claim_variant':['in',claim_variant]}, pluck='claim_key')))
                if len(claim_key) > 1:
                    log_error(str(claim_key),'Claim Key','Claim Key - Settlement Advice')
                    return
                    
                if not claim_key:
                    claim_key = self.create_claim_key(record.claim_id,doctype,record.name,claim_variant)
            
                record.set('claim_key', claim_key[0])

@frappe.whitelist()
def process(args):
    try:
        args=cast_to_dic(args)
        n = int(args["chunk_size"])
        # Skipping the bill claim_id and ma_claim_id which are 0, Avoiding the queue
        bill_records = frappe.db.sql("""SELECT name FROM tabBill 
                                     WHERE ( claim_id != '0' and claim_id != ' ' and claim_id IS NOT NULL and claim_key is NULL ) 
                                     or ( ma_claim_id != '0' and ma_claim_id != ' ' and ma_claim_id IS NOT NULL and ma_claim_key is NULL ) """,
                                     as_dict=True)

        bill_records = [i['name'] for i in bill_records]
        if bill_records:
            for i in range(0, len(bill_records), n):
                chunk_doc = chunk.create_chunk(args["step_id"])
                frappe.enqueue(BillClaimKeyMapper().process, job_name= "Claim Key Mapper in Bill", queue=args["queue"], is_async=True, timeout=18000, records = bill_records[i:i + n],chunk_doc=chunk_doc)
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
        claim_records = frappe.get_list("ClaimBook", filters={'al_key': '', 'cl_key': ''}, pluck='name')
        if claim_records:
            for i in range(0,len(claim_records),n):
                chunk_doc = chunk.create_chunk(args["step_id"])
                frappe.enqueue(ClaimBookClaimKeyMapper().process, job_name= "Claim Key Mapper in ClaimBook", queue=args["queue"], is_async=True, timeout=18000, records = claim_records[i:i + n],chunk_doc=chunk_doc)
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
        sa_records = frappe.get_list("Settlement Advice",
                        filters={'claim_key': '', 'claim_id': ['not in', ['', '00']]}, pluck='name')
        if sa_records:
            for i in range(0,len(sa_records),n):
                chunk_doc = chunk.create_chunk(args["step_id"])
                frappe.enqueue(SAClaimKeyMapper().process, job_name= "Claim Key Mapper in Settlement Advice", queue=args["queue"], is_async=True, timeout=18000, records = sa_records[i:i + n],chunk_doc=chunk_doc)
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')
        
def insert_claim_keys(name,claim_key,doctype):
	key_doc =frappe.new_doc(doctype)
	if doctype == 'Bill Claim Key':
		key_doc.bill = name
	else:
		key_doc.claimbook = name
	key_doc.claim_key = claim_key	
	key_doc.save()		
	frappe.db.commit()