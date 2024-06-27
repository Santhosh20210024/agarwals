import frappe
from frappe.model.document import Document

class ErrorRecordLog(Document):
	@staticmethod
	def clear_old_logs(days=180):
		from frappe.query_builder import Interval
		from frappe.query_builder.functions import Now
		table = frappe.qb.DocType("Error Record Log")
		frappe.db.delete(table, filters={table.modified < (Now() - Interval(days=days))})