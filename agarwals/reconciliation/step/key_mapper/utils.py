import frappe
from agarwals.reconciliation import chunk
from agarwals.utils.error_handler import log_error

def enqueue_record_processing(mapper_class, records_chunk, chunk_doc, args):
    frappe.enqueue(
        mapper_class(records_chunk).process, queue = args['queue'] , is_async=True, timeout=50000, chunk_doc = chunk_doc
    )

def handle_exception(step_id, exception):
    if step_id:
        chunk_doc = chunk.create_chunk(step_id)
        chunk.update_status(chunk_doc, "Error")
    log_error(str(exception), "Step")