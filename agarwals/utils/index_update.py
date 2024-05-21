import frappe

@frappe.whitelist()
def update_index():
	indexes=frappe.get_all('Index Updation')
	for index in indexes:
		index_doc=frappe.get_doc('Index Updation',index['name'])
		table=index_doc.doctype_name
		columns=(index_doc.indexing_columns).split(",")
		for column in columns:
			frappe.db.sql("""CREATE INDEX IF NOT EXISTS {index_column}_cg ON `tab{table}` ({column})""".format(index_column=column,table=table,column=column))
	print("finished")