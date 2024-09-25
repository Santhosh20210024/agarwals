# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	if filters.get("execute") != 1:
		return [], []
	condition = get_condition(filters)
	if not condition:
		condition = "exists (SELECT 1)"

	query = f"""SELECT
	tsi.name as Bill,
	tm.settlement_advice as `Settlement Advice`,
	tsi.posting_date as `Bill Date`,
	tsi.entity as Entity,
	tsi.region as Region,
	tsi.branch as Branch,
	tm.bank_transaction as `UTR Number`,
	ROUND(tm.approved_amount,0) as `Approved Amount`,
	ROUND(tsi.total) as `Claim Amount`,
	ROUND(tpe.paid_amount) as `Allocated Amt to Bill`,
	ROUND(tm.settled_amount) as `Settled Amount`,
	ROUND(tm.tds_amount) as `TDS Amount`,
	ROUND(tm.disallowance_amount) as `Disallowed Amount`,
	ABS(ROUND(tsi.total) - ROUND(tm.settled_amount) - ROUND(tm.tds_amount) - ROUND(tm.disallowance_amount)) as `Excess Amount`
FROM
	`tabMatcher` tm
JOIN `tabSales Invoice` tsi ON
	tm.sales_invoice = tsi.name
JOIN `tabPayment Entry` tpe ON
    tpe.custom_sales_invoice = tsi.name and tpe.reference_no = tm.bank_transaction
WHERE
	tm.match_logic IN ('MA5-BN', 'MA1-CN', 'MA3-CN')
	and tm.settled_amount + tm.tds_amount + tm.disallowance_amount > tsi.total
	and tm.disallowance_amount >= 0 
	and tm.name in (SELECT id FROM `tabMatcher Reference`)
	and {condition}; """

	data = frappe.db.sql(query, as_dict=True)

	columns = [
		{'fieldname':'Bill','label':'Bill','fieldtype':'Data'},
		{'fieldname': 'Settlement Advice', 'label': 'Settlement Advice', 'fieldtype': 'Data'},
		{'fieldname': 'Bill Date', 'label': 'Bill Date', 'fieldtype': 'Date'},
		{'fieldname': 'Entity', 'label': 'Entity', 'fieldtype': 'Data'},
		{'fieldname': 'Region', 'label': 'Region', 'fieldtype': 'Data'},
		{'fieldname': 'Branch', 'label': 'Branch', 'fieldtype': 'Data'},
		{'fieldname': 'UTR Number', 'label': 'UTR Number', 'fieldtype': 'Data'},
		{'fieldname': 'Approved Amount', 'label': 'Approved Amount', 'fieldtype': 'Currency'},
		{'fieldname': 'Claim Amount', 'label': 'Claim Amount', 'fieldtype': 'Currency'},
		{'fieldname': 'Allocated Amt to Bill', 'label': 'Allocated Amt to Bill', 'fieldtype': 'Currency'},
		{'fieldname': 'Settled Amount', 'label': 'Settled Amount', 'fieldtype': 'Currency'},
		{'fieldname': 'TDS Amount', 'label': 'TDS Amount', 'fieldtype': 'Currency'},
		{'fieldname': 'Disallowed Amount', 'label': 'Disallowed Amount', 'fieldtype': 'Currency'},
		{'fieldname': 'Excess Amount', 'label': 'Excess Amount', 'fieldtype': 'Currency'}
	]

	return columns, data

def get_condition(filters):
    field_and_condition = {'from_bill_date':'tsi.posting_date >= ','to_bill_date':'tsi.posting_date <= ','bill_region':'tsi.region IN ','bill_entity':'tsi.entity IN ','bill_branch':'tsi.branch IN '}
    conditions = []
    for filter in filters:
        if filter == 'execute':
            continue
        if filters.get(filter):
            value = filters.get(filter)
            if not isinstance(value,list):
                conditions.append(f"{field_and_condition[filter]} '{value}'")
                continue
            value = tuple(value)
            if len(value) == 1:
                value = "('" + value[0] + "')"
            conditions.append(f"{field_and_condition[filter]} {value}")
    return " and ".join(conditions)