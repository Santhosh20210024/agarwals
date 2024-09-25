import frappe
from datetime import date


def execute(filters=None):
    condition = get_condition(filters)
    if not condition:
        condition = "exists (SELECT 1)"

    query = f"""
		SELECT bill_branch as BRANCH,
			bill_entity as ENTITY,
			bank_entity as `BANK ENTITY`,
			bill as `BILL NO`,
			bank_account as `BANK ACCOUNT`,
			bank_utr as `UTR NUMBER`,
			narration as `NARRATION`,
			utr_date as `UTR DATE`,
			bill_customer as `PARTY`,
			payment_posting_date as `POSTING DATE`,
			AHCL as `AHCL`,
			AEHL as `AEHL`,
			AJE as `AJE`,
			AHCL + AEHL + AJE as `TOTAL COLLECTION`
			FROM (
			 SELECT
			 	tbt.name as bank_utr,
			 	tbt.bank_account as bank_account,
			 	tbt.description as narration,
			 	tbt.custom_entity as bank_entity,
			 	tbt.`date` as utr_date,
				tpe.branch as bill_branch,
				tpe.entity as bill_entity,
				tpe.reference_no as utr_number,
				CASE WHEN tbt.custom_entity = 'AHC' THEN tpe.paid_amount ELSE 0 END AS AHCL,
				CASE WHEN tbt.custom_entity = 'AEH' THEN tpe.paid_amount ELSE 0 END AS AEHL,
				CASE WHEN tbt.custom_entity = 'AJE' THEN tpe.paid_amount ELSE 0 END AS AJE,
				tpe.party_name as bill_customer,
				tpe.custom_sales_invoice as bill,
				tpe.posting_date as payment_posting_date
		FROM `tabPayment Entry` tpe 
		JOIN `tabBank Transaction` tbt ON tbt.name = tpe.reference_no WHERE tpe.status != 'Cancelled' AND {condition} )t1 ORDER BY bill_entity, bill_branch, bill;
    """

    if filters.get("execute") == 1:
        print(query)
        data = frappe.db.sql(query, as_dict=True)

    else:
        data = {}

    columns = [
        {"label": "Branch", "fieldname": "BRANCH", "fieldtype": "Data"},
        {"label": "Branch Entity", "fieldname": "ENTITY", "fieldtype": "Data"},
        {"label": "Bank Entity", "fieldname": "BANK ENTITY", "fieldtype": "Data"},
        {"label": "Bill No", "fieldname": "BILL NO", "fieldtype": "Data"},
        {"label": "Bank Account", "fieldname": "BANK ACCOUNT", "fieldtype": "Data"},
        {"label": "UTR Number", "fieldname": "UTR NUMBER", "fieldtype": "Data"},
        {"label": "Narration", "fieldname": "NARRATION", "fieldtype": "Data"},
        {"label": "UTR Date", "fieldname": "UTR DATE", "fieldtype": "Date"},
        {"label": "Party", "fieldname": "PARTY", "fieldtype": "Data"},
        {"label": "Posting Date", "fieldname": "POSTING DATE", "fieldtype": "Date"},
        {"label": "AHCL", "fieldname": "AHCL", "fieldtype": "Currency"},
        {"label": "AEHL", "fieldname": "AEHL", "fieldtype": "Currency"},
        {"label": "AJE", "fieldname": "AJE", "fieldtype": "Currency"},
        {
            "label": "Total Collection",
            "fieldname": "TOTAL COLLECTION",
            "fieldtype": "Currency",
        },
    ]

    return columns, data


def datetime_converter(o):
    if isinstance(o, date):
        return o.isoformat()


def get_condition(filters):
    field_and_condition = {'from_posting_date':'tpe.posting_date >= ','to_posing_date':'tpe.posting_date <= ','bill_entity':'tpe.entity in ', 'bill_branch':'tpe.branch in ', 'bank_account':'tbt.bank_account in ','bank_entity':'tbt.custom_entity in ','from_utr_date':'tbt.`date` >= ','to_utr_date':'tbt.`date` <= '}
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
