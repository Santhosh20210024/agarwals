# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    
	if not filters.get('from_date'):
		filters['from_date'] = '2001-01-01'
	if not filters.get('to_date'):
		filters['to_date'] = frappe.utils.today()
        
	query = """SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    ROUND(tbt.deposit) AS 'UTR Amount',
	    tsa.settled_amount AS 'Settled Amount',
	    tsa.tds_amount AS 'TDS Amount',
	    tsa.disallowed_amount AS 'Disallowed Amount'
	FROM
	    `tabBank Transaction` tbt
	JOIN `tabSettlement Advice` tsa ON
	    tsa.cg_utr_number = tbt.custom_cg_utr_number
	LEFT JOIN `tabBill` tbi ON
	    tbi.claim_key = tsa.claim_key
	LEFT JOIN `tabClaimBook` tcb ON 
	    tsa.claim_key = tcb.al_key
	WHERE
	    tsa.status IN ('Open', 'Warning')
	    AND tbt.status = 'Pending'
	    AND tbi.name IS NULL AND tbt.`date`>= %(from_date)s and tbt.`date`<= %(to_date)s

	UNION

	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    ROUND(tbt.deposit) AS 'UTR Amount',
	    tsa.settled_amount AS 'Settled Amount',
	    tsa.tds_amount AS 'TDS Amount',
	    tsa.disallowed_amount AS 'Disallowed Amount'
	FROM
	    `tabBank Transaction` tbt
	JOIN `tabSettlement Advice` tsa ON
	    tsa.cg_formatted_utr_number = tbt.custom_cg_utr_number
	LEFT JOIN `tabBill` tbi ON
	    tbi.claim_key = tsa.claim_key
	LEFT JOIN `tabClaimBook` tcb ON 
	    tsa.claim_key = tcb.al_key
	WHERE
	    tsa.status IN ('Open', 'Warning')
	    AND tbt.status = 'Pending'
	    AND tbi.name IS NULL AND tbt.`date`>= %(from_date)s and tbt.`date`<= %(to_date)s

	UNION

	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    ROUND(tbt.deposit) AS 'UTR Amount',
	    tsa.settled_amount AS 'Settled Amount',
	    tsa.tds_amount AS 'TDS Amount',
	    tsa.disallowed_amount AS 'Disallowed Amount'
	FROM
	    `tabBank Transaction` tbt
	JOIN `tabSettlement Advice` tsa ON
	    tsa.cg_utr_number = tbt.custom_cg_utr_number
	LEFT JOIN `tabBill` tbi ON
	    tbi.ma_claim_key = tsa.claim_key
	LEFT JOIN `tabClaimBook` tcb ON 
	    tsa.claim_key = tcb.al_key
	WHERE
	    tsa.status IN ('Open', 'Warning')
	    AND tbt.status = 'Pending'
	    AND tbi.name IS NULL AND tbt.`date`>= %(from_date)s and tbt.`date`<= %(to_date)s

	UNION

	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    ROUND(tbt.deposit) AS 'UTR Amount',
	    tsa.settled_amount AS 'Settled Amount',
	    tsa.tds_amount AS 'TDS Amount',
	    tsa.disallowed_amount AS 'Disallowed Amount'
	FROM
	    `tabBank Transaction` tbt
	JOIN `tabSettlement Advice` tsa ON
	    tsa.cg_formatted_utr_number = tbt.custom_cg_utr_number
	LEFT JOIN `tabBill` tbi ON
	    tbi.ma_claim_key = tsa.claim_key
	LEFT JOIN `tabClaimBook` tcb ON 
	    tsa.claim_key = tcb.al_key
	WHERE
	    tsa.status IN ('Open', 'Warning')
	    AND tbt.status = 'Pending'
	    AND tbi.name IS NULL AND tbt.`date`>= %(from_date)s and tbt.`date`<= %(to_date)s

	UNION

	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    ROUND(tbt.deposit) AS 'UTR Amount',
	    tsa.settled_amount AS 'Settled Amount',
	    tsa.tds_amount AS 'TDS Amount',
	    tsa.disallowed_amount AS 'Disallowed Amount'
	FROM
	    `tabBank Transaction` tbt
	JOIN `tabSettlement Advice` tsa ON
	    tsa.cg_utr_number = tbt.custom_cg_utr_number
	LEFT JOIN `tabBill` tbi ON
	    tbi.claim_key = tsa.claim_key
	LEFT JOIN `tabClaimBook` tcb ON 
	    tsa.claim_key = tcb.cl_key
	WHERE
	    tsa.status IN ('Open', 'Warning')
	    AND tbt.status = 'Pending'
	    AND tbi.name IS NULL AND tbt.`date`>= %(from_date)s and tbt.`date`<= %(to_date)s

	UNION

	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    ROUND(tbt.deposit) AS 'UTR Amount',
	    tsa.settled_amount AS 'Settled Amount',
	    tsa.tds_amount AS 'TDS Amount',
	    tsa.disallowed_amount AS 'Disallowed Amount'
	FROM
	    `tabBank Transaction` tbt
	JOIN `tabSettlement Advice` tsa ON
	    tsa.cg_formatted_utr_number = tbt.custom_cg_utr_number
	LEFT JOIN `tabBill` tbi ON
	    tbi.claim_key = tsa.claim_key
	LEFT JOIN `tabClaimBook` tcb ON 
	    tsa.claim_key = tcb.cl_key
	WHERE
	    tsa.status IN ('Open', 'Warning')
	    AND tbt.status = 'Pending'
	    AND tbi.name IS NULL AND tbt.`date`>= %(from_date)s and tbt.`date`<= %(to_date)s

	UNION

	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    ROUND(tbt.deposit) AS 'UTR Amount',
	    tsa.settled_amount AS 'Settled Amount',
	    tsa.tds_amount AS 'TDS Amount',
	    tsa.disallowed_amount AS 'Disallowed Amount'
	FROM
	    `tabBank Transaction` tbt
	JOIN `tabSettlement Advice` tsa ON
	    tsa.cg_utr_number = tbt.custom_cg_utr_number
	LEFT JOIN `tabBill` tbi ON
	    tbi.ma_claim_key = tsa.claim_key
	LEFT JOIN `tabClaimBook` tcb ON 
	    tsa.claim_key = tcb.cl_key
	WHERE
	    tsa.status IN ('Open', 'Warning')
	    AND tbt.status = 'Pending'
	    AND tbi.name IS NULL AND tbt.`date`>= %(from_date)s and tbt.`date`<= %(to_date)s

	UNION

	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    ROUND(tbt.deposit) AS 'UTR Amount',
	    tsa.settled_amount AS 'Settled Amount',
	    tsa.tds_amount AS 'TDS Amount',
	    tsa.disallowed_amount AS 'Disallowed Amount'
	FROM
	    `tabBank Transaction` tbt
	JOIN `tabSettlement Advice` tsa ON
	    tsa.cg_formatted_utr_number = tbt.custom_cg_utr_number
	LEFT JOIN `tabBill` tbi ON
	    tbi.ma_claim_key = tsa.claim_key
	LEFT JOIN `tabClaimBook` tcb ON 
	    tsa.claim_key = tcb.cl_key
	WHERE
	    tsa.status IN ('Open', 'Warning')
	    AND tbt.status = 'Pending'
	    AND tbi.name IS NULL AND tbt.`date`>= %(from_date)s and tbt.`date`<= %(to_date)s;
    """
	data = frappe.db.sql(query ,filters, as_dict = True)
 
	columns = [
        {"label": "UTR Number", "fieldname": "utr_number", "fieldtype": "Data"},
        {"label": "UTR Date", "fieldname": "utr_date", "fieldtype": "Date"},
        {"label": "Bank Entity", "fieldname": "bank_entity", "fieldtype": "Data"},
        {"label": "Bank Region", "fieldname": "bank_region", "fieldtype": "Data"},
        {"label": "SA Claim ID", "fieldname": "sa_claim_id", "fieldtype": "Data"},
        {"label": "AL Number", "fieldname": "al_number", "fieldtype": "Data"},
        {"label": "CL Number", "fieldname": "cl_number", "fieldtype": "Data"},
        {"label": "CB Bill Number", "fieldname": "cb_bill_number", "fieldtype": "Data"},
        {"label": "UTR Amount", "fieldname": "utr_amount", "fieldtype": "Currency"},
        {"label": "Settled Amount", "fieldname": "settled_amount", "fieldtype": "Currency"},
        {"label": "TDS Amount", "fieldname": "tds_amount", "fieldtype": "Currency"},
        {"label": "Disallowed Amount", "fieldname": "disallowed_amount", "fieldtype": "Currency"}
    ]
 
	return columns, data
