import frappe

@frappe.whitelist()
def update_index( name = None):
    if name:
        index_updation_list = frappe.get_all('Index Updation',filters={'name': name})
    else:
        index_updation_list = frappe.get_all('Index Updation')
    for _index in index_updation_list:
        index_doc = frappe.get_doc('Index Updation', _index['name'])
        doctype_name = index_doc.doctype_name
        indexing_columns = (index_doc.indexing_columns).split(",")
        for column in indexing_columns:
            frappe.db.sql("""CREATE INDEX IF NOT EXISTS {index_column}_cg ON `tab{table}` ({column})""".format(index_column = column,table = doctype_name,column = column))
        frappe.db.commit()