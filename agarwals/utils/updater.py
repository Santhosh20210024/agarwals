import frappe

@frappe.whitelist()
def update_utr_in_separate_column():
    utr_in_claimbook_update_query = "UPDATE `tabClaimBook` SET cg_utr_number = TRIM(TRIM(LEADING '0' FROM utr_number)), cg_formatted_utr_number = TRIM(TRIM(LEADING '0' FROM final_utr_number))"
    utr_in_settlement_advice_update_query = "UPDATE `tabSettlement Advice` SET cg_utr_number = TRIM(TRIM(LEADING '0' FROM utr_number)), cg_formatted_utr_number = TRIM(TRIM(LEADING '0' FROM final_utr_number))"
    utr_in_bank_transaction_update_query = "UPDATE `tabBank Transaction` SET custom_cg_utr_number = TRIM(TRIM(LEADING '0' FROM reference_number))"
    
    frappe.db.sql(utr_in_bank_transaction_update_query)
    frappe.db.sql(utr_in_settlement_advice_update_query)
    frappe.db.sql(utr_in_claimbook_update_query)
    frappe.db.commit()

@frappe.whitelist()
def update_bill_no_separate_column():
    bill_no_advice_update_query = "UPDATE `tabSettlement Advice` SET cg_formatted_bill_number = LOWER(TRIM(REPLACE(bill_no,':','')))"
    bill_no_debtors_update_query = "UPDATE `tabBill` SET cg_formatted_bill_number = LOWER(TRIM(REPLACE(bill_no,':','')))"
    bill_no_claim_update_query_ma = "UPDATE `tabClaimBook` SET cg_formatted_bill_number = LOWER(TRIM(REPLACE(ma_bill_no,':',''))) where ma_bill_no is not null"
    bill_no_claim_update_query = "UPDATE `tabClaimBook` SET cg_formatted_bill_number = LOWER(TRIM(REPLACE(final_bill_number,':',''))) where ma_bill_no is null"
    
    frappe.db.sql(bill_no_advice_update_query)
    frappe.db.sql(bill_no_debtors_update_query)
    frappe.db.sql(bill_no_claim_update_query_ma)
    frappe.db.sql(bill_no_claim_update_query)
    frappe.db.commit()

