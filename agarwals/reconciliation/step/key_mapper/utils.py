import frappe
from agarwals.reconciliation import chunk
from agarwals.utils.error_handler import log_error

def enqueue_record_processing(mapper_class, records_chunk, chunk_doc, args):
    try:
        frappe.enqueue(
            mapper_class(records_chunk, chunk_doc).process, queue = args['queue'] , is_async=True, timeout=50000
        )
    except Exception as err:
        chunk.update_status(chunk_doc, "Error")
        log_error(err, eval(mapper_class))