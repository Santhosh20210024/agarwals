# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if filters.get('execute') != 1:
        return [], []
    condition = get_condition(filters)
    if not condition:
        condition = "exists (SELECT 1)"

    query = f"""SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tbt.bank_account AS 'Bank Account',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    tbt.deposit AS 'UTR Amount',
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
	    AND tbi.name IS NULL AND {condition}
	UNION
	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tbt.bank_account AS 'Bank Account',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    tbt.deposit AS 'UTR Amount',
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
	    AND tbi.name IS NULL AND {condition}
	UNION
	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tbt.bank_account AS 'Bank Account',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    tbt.deposit AS 'UTR Amount',
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
	    AND tbi.name IS NULL AND {condition}
	UNION
	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tbt.bank_account AS 'Bank Account',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    tbt.deposit AS 'UTR Amount',
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
	    AND tbi.name IS NULL AND {condition}
	UNION
	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tbt.bank_account AS 'Bank Account',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    tbt.deposit AS 'UTR Amount',
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
	    AND tbi.name IS NULL AND {condition}
	UNION
	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tbt.bank_account AS 'Bank Account',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    tbt.deposit AS 'UTR Amount',
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
	    AND tbi.name IS NULL AND {condition}
	UNION
	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tbt.bank_account AS 'Bank Account',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    tbt.deposit AS 'UTR Amount',
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
	    AND tbi.name IS NULL AND {condition}
	UNION
	SELECT
	    tbt.custom_cg_utr_number AS 'UTR Number',
	    tbt.`date` AS 'UTR Date',
	    tbt.custom_entity AS 'Bank Entity',
	    tbt.custom_region AS 'Bank Region',
	    tbt.bank_account AS 'Bank Account',
	    tsa.claim_id AS 'SA Claim ID',
	    tcb.al_number AS 'AL Number',
	    tcb.cl_number AS 'CL Number',
	    tcb.final_bill_number AS 'CB Bill Number',
	    tbt.deposit AS 'UTR Amount',
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
	    AND tbi.name IS NULL AND {condition};
    """

    data = frappe.db.sql(query, filters, as_dict=True)

    columns = [
        {"label": "UTR Number", "fieldname": "UTR Number", "fieldtype": "Data"},
        {"label": "UTR Date", "fieldname": "UTR Date", "fieldtype": "Date"},
        {"label": "Bank Entity", "fieldname": "Bank Entity", "fieldtype": "Data"},
        {"label": "Bank Region", "fieldname": "Bank Region", "fieldtype": "Data"},
        {"label": "Bank Account", "fieldname": "Bank Account", "fieldtype": "Data"},
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


def get_condition(filters):
    conditions = []
    field_and_condition = {
        'from_utr_date': 'tbt.`date` <= ',
        'to_utr_date': 'tbt.`date` >= ',
        'bank_account': 'tbt.`bank_account` IN ',
        'bank_entity': 'tbt.`custom_entity` IN ',
        'bank_region': 'tbt.`custom_region` IN '
    }
    for filter in filters:
        if filter == 'execute':
            continue
        if filters.get(filter):
            value = filters.get(filter)
            if not isinstance(value, list):
                conditions.append(f"{field_and_condition[filter]} '{value}'")
                continue
            value = tuple(value)
            if len(value) == 1:
                value = "('" + value[0] + "')"
            conditions.append(f"{field_and_condition[filter]} {value}")
    return " and ".join(conditions)
