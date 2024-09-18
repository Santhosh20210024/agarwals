import frappe
from agarwals.reconciliation import chunk
from agarwals.utils.error_handler import log_error

def enqueue_record_processing(mapper_class, records_chunk, chunk_doc, args, job_name):
    try:
        frappe.enqueue(
            mapper_class(records_chunk, chunk_doc).process, queue = args['queue'] , is_async=True, timeout=50000, job_name = job_name
        )
    except Exception as err:
        chunk.update_status(chunk_doc, "Error")
        log_error(err, str(mapper_class))

def process_records(query, mapper_class, chunk_size, args):
    records = frappe.db.sql(query, as_dict=True)
    if records:
        for index in range(0, len(records), chunk_size):
            chunk_doc = chunk.create_chunk(args.get("step_id"))
            records_chunk = records[index : index + chunk_size]
            enqueue_record_processing(mapper_class, records_chunk, chunk_doc, args, job_name = "Claim key Creator")
    else:
        chunk_doc = chunk.create_chunk(args.get("step_id"))
        chunk.update_status(chunk_doc, "Processed")