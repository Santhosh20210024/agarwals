import frappe
from frappe.utils.caching import redis_cache


def create_chunk(step_id):
    if not step_id or step_id == '':
        return None
    chunk = frappe.new_doc("Chunk")
    chunk.step_id = step_id
    chunk.save()
    frappe.db.commit()
    return chunk


def update_status(chunk, status):
    if not chunk or chunk == '':
        return None
    chunk.status = status
    chunk.save()
    frappe.db.commit()


@redis_cache
def get_status(chunk_status: str = "Processed", process_status: str = "Processed") -> str:
    """
        Used find the overall chunk status where you have a multiple process return its current status
        :param chunk_status: This is the current status of the overall process
        :param process_status: This is the current status of the current process
    """
    if chunk_status == "Error" or process_status == "Error":
        return "Error"
    return "Processed"
