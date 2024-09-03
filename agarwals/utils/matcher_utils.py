import frappe

@frappe.whitelist()
def update_bill_no_separate_column():
    bill_no_advice_update_query = "UPDATE `tabSettlement Advice` SET cg_formatted_bill_number = LOWER(TRIM(REPLACE(bill_no,':',''))) WHERE cg_formatted_bill_number is null"
    bill_no_debtors_update_query = "UPDATE `tabBill` SET cg_formatted_bill_number = LOWER(TRIM(REPLACE(bill_no,':',''))) WHERE cg_formatted_bill_number is null"
    bill_no_claim_update_query_ma = "UPDATE `tabClaimBook` SET cg_formatted_bill_number = LOWER(TRIM(REPLACE(ma_bill_no,':',''))) where ma_bill_no is not null"
    bill_no_claim_update_query = "UPDATE `tabClaimBook` SET cg_formatted_bill_number = LOWER(TRIM(REPLACE(final_bill_number,':',''))) where ma_bill_no is null"
    
    frappe.db.sql(bill_no_advice_update_query)
    frappe.db.sql(bill_no_debtors_update_query)
    frappe.db.sql(bill_no_claim_update_query_ma)
    frappe.db.sql(bill_no_claim_update_query)