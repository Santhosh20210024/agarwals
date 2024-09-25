# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	condition = get_condition(filters)
	if not condition:
		condition = "exists (SELECT 1)"

	query = f"""SELECT
    	bt.custom_entity as custom_entity,
		bt.custom_region as custom_region,
		bt.`date` as `date`,
		bt.name as name,
		bt.bank_account as bank_account,
		ROUND(bt.allocated_amount,0) as allocated,
		ROUND(bt.unallocated_amount,0) as unallocated,
		bt.description as description
	FROM
		`tabBank Transaction` AS bt
	LEFT JOIN
		`tabSettlement Advice` AS tsa
	ON bt.custom_utr_key = sa.utr_key
	WHERE
		status in ('Unreconciled','Pending') AND {condition} AND tsa.name IS NULL"""

	if filters.get('execute') == 1:
		data = frappe.db.sql(query, as_dict=True)
	else:
		data = {}

	columns = [{
		'label':"Entity",
		'fieldname':"custom_entity",
		'fieldtype':"Data"
	},
		{
			'label': "Region",
			'fieldname': "custom_region",
			'fieldtype': "Data"
		},
		{
			'label': "UTR Date",
			'fieldname': "date",
			'fieldtype': "Date"
		},
		{
			'label': "UTR Number",
			'fieldname': "name",
			'fieldtype': "Link",
			'options': "Bank Transaction"
		},
		{
			'label': "Bank Account",
			'fieldname': "bank_account",
			'fieldtype': "Data"
		},
		{
			'label': "Allocated",
			'fieldname': "allocated",
			'fieldtype': "Currency"
		},
		{
			'label': "UnAllocated",
			'fieldname': "unallocated",
			'fieldtype': "Currency"
		},
		{
			'label': "Description",
			'fieldname': "description",
			'fieldtype': "Data"
		},
	]



	return columns, data


def get_condition(filters):
	field_and_condition = {'from_utr_date':'date >= ','to_utr_date':'date <= ','region':'custom_region in ', 'entity':'custom_entity in ', 'bank_account':'bank_account in '}
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
