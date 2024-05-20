from agarwals.reconciliation.job.processor import Processor
import frappe

class ChunkProcessor(Processor):
    def __init__(self):
        super().__init__()
        self.doc_name = "Chunk"
        self.parent_field_name = "step_id"
        self.parent_doc_name = "Step"
