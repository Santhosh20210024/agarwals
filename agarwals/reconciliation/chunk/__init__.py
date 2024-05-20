import frappe

def create_chunk(step_id):
    if not step_id:
        return None
    chunk = frappe.new_doc("Chunk")
    chunk.step_id = step_id
    chunk.save()
    frappe.db.commit()
    return chunk

def update_status(chunk, status):
    if not chunk:
        return None
    chunk.status = status
    chunk.save()
    frappe.db.commit()