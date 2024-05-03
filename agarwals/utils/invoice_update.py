import frappe

def status_update():
   frappe.db.sql("""update `tabSales Invoice` set status ='Partly Paid' where outstanding_amount != rounded_total and status ='Overdue';""")
   frappe.db.sql("""update `tabSales Invoice` set status ='Unpaid' where status = 'Overdue';""")
   frappe.db.commit()