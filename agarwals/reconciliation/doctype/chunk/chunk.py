# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from agarwals.reconciliation.chunk.chunk_processor import ChunkProcessor
class Chunk(Document):

	def on_update(self):
		ChunkProcessor().process(self.name, self.step_id)
