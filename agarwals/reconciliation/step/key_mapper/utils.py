import frappe

def enqueue_record_processing(mapper_class, records_chunk):  # not closed
    frappe.enqueue(
        mapper_class(records_chunk).process, queue="long", is_async=True, timeout=50000
    )
    #mapper_class(records_chunk).process()

# def finalize_chunk_processing(step_id): # not closed
#     chunk_doc = chunk.create_chunk(step_id)
#     chunk.update_status(chunk_doc, "Processed")


# def handle_exception(step_id, exception): # not closed
#     if step_id:
#         chunk_doc = chunk.create_chunk(step_id)
#         chunk.update_status(chunk_doc, "Error")
#     log_error(str(exception), "Step")