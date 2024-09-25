# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if filters.get("execute") != 1:
        return [],[]
    condition = get_condition(filters)
    if not condition:
        condition = "exists (SELECT 1)"
    query = f"""with advice as(
select
	tsa.cg_formatted_utr_number
from
	`tabSettlement Advice` tsa
where
	tsa.cg_formatted_utr_number in (
	select
		tsa.cg_formatted_utr_number
	from
		`tabSettlement Advice` tsa
	where
		tsa.tds_amount <> 0.000000000
	group by
		tsa.cg_formatted_utr_number
	having
		count(tsa.cg_formatted_utr_number) > 1)
	and tds_amount = 0.000000000 
)
select
	sa.source_file as FILE_ID,
	sa.file_name as FILE_Name,
	sa.name as ADVICE_ID,
	sa.status as STATUS,
	sa.paid_date as SETTLED_DATE,
	sa.bill_no as BILL_NO,
	sa.claim_id as CLAIM_ID,
	sa.utr_number as UTR_NUMBER,
	sa.cg_formatted_utr_number as CG_UTR_NUMBER,
	ROUND(sa.claim_amount,0) as CLAIM_AMOUNT,
	ROUND(bt.deposit,0) as BANK_DEPOSIT,
	ROUND(sa.settled_amount,0) as SETTLED_AMOUNT,
	ROUND(sa.tds_amount,0) as TDS_AMOUNT,
	ROUND(sa.disallowed_amount,0) as DISALLOWED_AMOUNT,
	sa.payers_remark as PAYER_REMARKS
from
	`tabSettlement Advice` sa RIGHT JOIN `tabBank Transaction` as bt
on sa.cg_formatted_utr_number = bt.custom_cg_utr_number	
where
	sa.cg_formatted_utr_number in (
	select
		*
	from
		advice)  and {condition}
    order by sa.cg_formatted_utr_number;

    """
    columns = [
        {
            "fieldname": "FILE_ID",
            "label": "FILE ID",
            "fieldtype": "Data",
        },
        {
            "fieldname": "FILE_Name",
            "label": "FILE Name",
            "fieldtype": "Data",
        },
        {
            "fieldname": "ADVICE_ID",
            "label": "ADVICE ID",
            "fieldtype": "Data",
        },
        {
            "fieldname": "STATUS",
            "label": "STATUS",
            "fieldtype": "Data",
        },
        {
            "fieldname": "SETTLED_DATE",
            "label": "PAID DATE",
            "fieldtype": "Date",
        },
        {
            "fieldname": "BILL NO",
            "label": "BILL NO",
            "fieldtype": "Data",
        },
        {
            "fieldname": "CLAIM_ID",
            "label": "CLAIM ID",
            "fieldtype": "Data",
        },
        {
            "fieldname": "UTR_NUMBER",
            "label": "UTR NUMBER",
            "fieldtype": "Data",
        },
        {
            "fieldname": "CG_UTR_NUMBER",
            "label": "CG UTR NUMBER",
            "fieldtype": "Data",
        },
        {
            "fieldname": "CLAIM_AMOUNT",
            "label": "CLAIM AMOUNT",
            "fieldtype": "Float",
        },
        {
            "fieldname": "BANK_DEPOSIT",
            "label": "BANK DEPOSIT",
            "fieldtype": "Float",
        },
        {
            "fieldname": "SETTLED_AMOUNT",
            "label": "SETTLED AMOUNT",
            "fieldtype": "Float",
        },
        {
            "fieldname": "TDS_AMOUNT",
            "label": "TDS AMOUNT",
            "fieldtype": "Float",
        },
        {
            "fieldname": "DISALLOWED_AMOUNT",
            "label": "DISALLOWED AMOUNT",
            "fieldtype": "Float",
        },
        {
            "fieldname": "PAYER_REMARKS",
            "label": "PAYER REMARKS",
            "fieldtype": "Data",
        }
    ]
    data = frappe.db.sql(query , as_dict = True)
    return columns, data

def get_condition(filters):
    field_and_condition = {'status':'sa.status in ','from_paid_date':'sa.paid_date >= ','to_paid_date':'sa.paid_date <= '}
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