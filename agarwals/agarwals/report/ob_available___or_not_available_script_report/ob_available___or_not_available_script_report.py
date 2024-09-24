# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
        
	query = """SELECT
		tb.name AS 'Bill',
		tb.branch AS 'Bill Branch',
		tb.region AS 'Bill Region',
		tb.entity AS 'Bill Entity',
		tb.claim_id AS 'Claim ID',
		tb.claim_amount AS 'Claim Amount',
		tbt1.name AS 'UTR Number',
		tbt1.deposit AS 'Deposit Amount',
		tbt1.bank_account as 'Bank Account',
		tbt1.custom_region AS 'Bank Region',
		tbt1.custom_entity AS 'Bank Entity'
	FROM
		`tabBill` tb
	JOIN `tabSales Invoice` tsi ON
		tb.name = tsi.name
	JOIN `tabSettlement Advice` tsa1 ON
		tb.claim_key = tsa1.claim_key
	JOIN `tabSettlement Advice` tsa2 ON
		tb.ma_claim_key = tsa2.claim_key
	JOIN `tabBank Transaction` tbt1 ON
		tsa1.cg_utr_number = tbt1.custom_cg_utr_number
	JOIN `tabBank Transaction` tbt2 ON
		tsa2.cg_utr_number = tbt2.custom_cg_utr_number
	JOIN `tabBank Transaction` tbt3 ON
		tsa1.cg_formatted_utr_number = tbt3.custom_cg_utr_number
	JOIN `tabBank Transaction` tbt4 ON
		tsa1.cg_formatted_utr_number = tbt4.custom_cg_utr_number
	WHERE
		tsi.status = 'Unpaid'
		AND (tbt1.status = 'Reconciled'
			OR tbt2.status = 'Reconciled')
		AND (tsa1.status IN ('Open','Error','Warning')
			OR tsa2.status IN ('Open','Error','Warning'));
	    """
	data = frappe.db.sql(query , as_dict = True)
 
	columns = [
        {"label": "Bill", "fieldname": "Bill", "fieldtype": "Data"},
        {"label": "Bill Branch", "fieldname": "Bill Branch", "fieldtype": "Data"},
        {"label": "Bill Region", "fieldname": "Bill Region", "fieldtype": "Data"},
        {"label": "Bill Entity", "fieldname": "Bill Entity", "fieldtype": "Data"},
        {"label": "Claim ID", "fieldname": "Claim ID", "fieldtype": "Data"},
        {"label": "Claim Amount", "fieldname": "Claim Amount", "fieldtype": "Currency"},
        {"label": "UTR Number", "fieldname": "UTR number", "fieldtype": "Data"},
        {"label": "Deposit Amount", "fieldname": "Deposit Amount", "fieldtype": "Currency"},
        {"label": "Bank Account", "fieldname": "Bank Account", "fieldtype": "Data"},
        {"label": "Bank Region", "fieldname": "Bank Region", "fieldtype": "Data"},
        {"label": "Bank Entity", "fieldname": "Bank_Entity", "fieldtype": "Data"}
    ]
 
	return columns, data
