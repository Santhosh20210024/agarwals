# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):

    query = """SELECT
	CASE
		WHEN row_count = 1 THEN name
		ELSE NULL
	END as bill,
	match_logic,
	settlement_advice,
	payers_remark 
    FROM
	`viewSales Invoice Payers Remark` vsipr;
     """
    columns = [
        {"label": "Bill", "fieldname": "bill", "fieldtype": "Data"},
        {"label": "Match Logic", "fieldname": "match_logic", "fieldtype": "Data"},
        {
            "label": "Settlement Advice",
            "fieldname": "settlement_advice",
            "fieldtype": "Data",
        },
        {"label": "Payers Remark", "fieldname": "payers_remark", "fieldtype": "Data"},
    ]

    data = frappe.db.sql(query, as_dict=True)
    return columns, data
