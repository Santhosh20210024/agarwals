import frappe
from agarwals.utils.utr_key_creator import UTRKeyCreator
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.reconciliation import chunk
from agarwals.utils.error_handler import log_error

class UTRKeyMapper:

    def get_record_obj(self, name):
        return None

    def get_utr_numbers(self, record):
        return []

    def map_utr_keys(self, record):
        return None, None
    
    def get_variants(self, utr_number, doctype, name):
        return UTRKeyCreator(utr_number, doctype, name).get_variants()

    def create_utr_key(self, utr_number, doctype, name, utr_variant):
        return UTRKeyCreator(utr_number, doctype, name).process(utr_variant)

    def process(self, records, chunk_doc):
        chunk.update_status(chunk_doc, "InProgress")
        try:
            for record in records:
                record_obj = self.get_record_obj(record)
                self.map_utr_keys(record_obj)
                record_obj.save()
            frappe.db.commit()
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")

class BankTransactionUTRKeyMapper(UTRKeyMapper):

    def get_record_obj(self, name):
        return frappe.get_doc('Bank Transaction', name)

    def get_doctype(self):
        return 'Bank Transaction'

    def map_utr_keys(self, record):
        doctype = self.get_doctype()

        if(record.reference_number != '0' and record.status != 'Cancelled'):
                utr_variant = list(self.get_variants(record.reference_number.lower().strip(), doctype, record.name))
                utr_key = list(set(frappe.get_list("UTR Key", filters={'utr_variant':['in', utr_variant]}, pluck='utr_key')))
                
                if len(utr_key) > 1: # Check if any case it happening 
                    log_error(str(utr_key),'UTR Key', 'UTR Key - Bank Transaction') 
                    return
                if not utr_key:
                    utr_key = self.create_utr_key(record.reference_number.lower().strip(), doctype, record.name, utr_variant)
                record.set('custom_utr_key' , utr_key[0])

class SettlementAdviceUTRKeyMapper(UTRKeyMapper):

    def get_record_obj(self, name):
        return frappe.get_doc('Settlement Advice', name)

    def get_doctype(self):
        return 'Settlement Advice'

    def map_utr_keys(self, record):
        doctype = self.get_doctype()

        if record.utr_number != '0' and record.utr_number is not None:
            if str(record.utr_number).strip():
                utr_variant = list(self.get_variants(record.utr_number.lower().strip(), doctype, record.name))
                utr_key = list(set(frappe.get_list("UTR Key", filters={'utr_variant':['in',utr_variant]}, pluck='utr_key')))
                
                if len(utr_key) > 1: # Check if any case it happening 
                    log_error(str(utr_key),'UTR Key', 'UTR Key - Settlement Advice') 
                    return
                
                if not utr_key:
                    utr_key = self.create_utr_key(record.utr_number.lower().strip(), doctype, record.name, utr_variant)
                    
                record.set('utr_key', utr_key[0])

class ClaimBookUTRKeyMapper(UTRKeyMapper):

    def get_record_obj(self, name):
        return frappe.get_doc('ClaimBook', name)

    def get_doctype(self):
        return 'ClaimBook'

    def map_utr_keys(self, record):
        doctype = self.get_doctype()

        if record.utr_number != '0' and record.utr_number is not None:
            if str(record.utr_number).strip():
                utr_variant = list(self.get_variants(record.utr_number.lower().strip(), doctype, record.name))
                utr_key = list(set(frappe.get_list("UTR Key", filters={'utr_variant':['in',utr_variant]}, pluck='utr_key')))
                
                if len(utr_key) > 1: # Check if any case it happening 
                    log_error(str(utr_key),'UTR Key', 'UTR Key - ClaimBook') 
                    return
                
                if not utr_key:
                    utr_key = self.create_utr_key(record.utr_number.lower(),doctype,record.name,utr_variant)
                    
                record.set('utr_key', utr_key[0])
            
@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        chunk_size = int(args["chunk_size"])

        # Process Bank Transactions
        process_records(
            """SELECT name FROM `tabBank Transaction`
               WHERE ( reference_number != '0' and reference_number IS NOT NULL and custom_utr_key IS NULL 
               and status != 'Cancelled' )""",
            BankTransactionUTRKeyMapper,
            chunk_size,
            args,
        )

        # Process Claim Book records
        process_records(
            """SELECT name FROM `tabClaimBook` 
               WHERE  utr_number != '0' and utr_number IS NOT NULL and utr_key IS NULL""",
            ClaimBookUTRKeyMapper,
            chunk_size,
            args,
        )
        

        # Process Settlement Advice records
        process_records(
            """SELECT name FROM `tabSettlement Advice` 
               WHERE utr_number !='0' and utr_number IS NOT NULL and utr_key IS NULL""",
            SettlementAdviceUTRKeyMapper,
            chunk_size,
            args,
        )

    except Exception as e:
        handle_exception(args["step_id"], e)

def process_records(query, mapper_class, chunk_size, args):
    records = frappe.db.sql(query, as_list=True)
    if records:
        for index in range(0, len(records), chunk_size):
            chunk_doc = chunk.create_chunk(args["step_id"])
            frappe.enqueue(
                mapper_class().process,
                queue = args['queue'],
                is_async = True,
                timeout = 50000,
                records = records[index : index + chunk_size],
                chunk_doc = chunk_doc,
            )
            # mapper_class().process(records,chunk_doc)
    else:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Processed")

def handle_exception(step_id, exception):
    chunk_doc = chunk.create_chunk(step_id)
    chunk.update_status(chunk_doc, "Error")
    log_error(exception, 'Step')