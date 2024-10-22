import time
import frappe
from agarwals.reconciliation import chunk
from agarwals.reconciliation.job import run

def test(chunk_doc):
    chunk.update_status(chunk_doc, "InProgress")
    time.sleep(5)
    chunk.update_status(chunk_doc, "Processed")

@frappe.whitelist()
def process(args):
    chunk_size = int(args["chunk_size"])
    for i in range(chunk_size):
        chunk_doc = chunk.create_chunk(args["step_id"])
        # test(chunk_doc)
        frappe.enqueue(test, queue=args["queue"], is_async=True, timeout=18000, chunk_doc=chunk_doc)

@frappe.whitelist()
def start():
    run("reconciliation_cron")