# # Copyright (c) 2024, Agarwals and contributors
# # For license information, please see license.txt

import frappe
from frappe.model.document import Document
from agarwals.reconciliation.step.step_processor import StepProcessor
from agarwals.reconciliation.job.processor import Processor


class Step(Document, Processor):
	    
	def on_update(self):
		StepProcessor().process(self.name, self.job_id)
			





