import frappe


def execute():
    # Created a view that contains data based on MRN checks for reinstated cancelled bills.
    frappe.db.sql("""
        CREATE OR REPLACE ALGORITHM = UNDEFINED VIEW viewcancelled_bills AS
        SELECT tsi.*, tb.name AS bill_name  
        FROM `tabSales Invoice` tsi 
        JOIN tabBill tb  ON tb.mrn = tsi.custom_mrn 
        WHERE tb.status = 'CANCELLED'
        ;
    """)