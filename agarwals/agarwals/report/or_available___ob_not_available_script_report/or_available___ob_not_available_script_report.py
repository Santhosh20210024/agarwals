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
        {"label": "UTR Number", "fieldname": "UTR Number", "fieldtype": "Data"},
        {"label": "UTR Date", "fieldname": "UTR Date", "fieldtype": "Date"},
        {"label": "Bank Entity", "fieldname": "Bank Entity", "fieldtype": "Data"},
        {"label": "Bank Region", "fieldname": "Bank Region", "fieldtype": "Data"},
        {"label": "SA Claim ID", "fieldname": "SA Claim ID", "fieldtype": "Data"},
        {"label": "AL Number", "fieldname": "AL Number", "fieldtype": "Data"},
        {"label": "CL Number", "fieldname": "CL Number", "fieldtype": "Data"},
        {"label": "CB Bill Number", "fieldname": "CB Bill Number", "fieldtype": "Data"},
        {"label": "UTR Amount", "fieldname": "UTR Amount", "fieldtype": "Currency"},
        {"label": "Settled Amount", "fieldname": "Settled Amount", "fieldtype": "Currency"},
        {"label": "TDS Amount", "fieldname": "TDS Amount", "fieldtype": "Currency"},
        {"label": "Disallowed Amount", "fieldname": "Disallowed Amount", "fieldtype": "Currency"}
    ]
 
	return columns, data
