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
				CASE
					WHEN row_count = 1 THEN t.`bill_number`
					ELSE NULL
				END AS `Bill Number`,
				CASE
					WHEN row_count = 1 THEN t.`bill_date`
					ELSE NULL
				END AS `Bill Date`,
				CASE
					WHEN row_count = 1 THEN t.`entity`
					ELSE NULL
				END AS `Entity`,
				CASE
					WHEN row_count = 1 THEN t.`region`
					ELSE NULL
				END AS `Region`,
				CASE
					WHEN row_count = 1 THEN t.`branch`
					ELSE NULL
				END AS `Branch`,
				CASE
					WHEN row_count = 1 THEN t.`branch_type`
					ELSE NULL
				END AS `Branch Type`,
				CASE
					WHEN row_count = 1 THEN t.`customer`
					ELSE NULL
				END AS `Customer`,
				CASE
					WHEN row_count = 1 THEN t.`customer_group`
					ELSE NULL
				END AS `Customer Group`,
				CASE
					WHEN row_count = 1 THEN t.`claim_id`
					ELSE NULL
				END AS `Claim ID`,
				CASE
					WHEN row_count = 1 THEN t.`ma_claim_id`
					ELSE NULL
				END AS `MA Claim ID`,
				CASE
					WHEN row_count = 1 THEN t.`patient_name`
					ELSE NULL
				END AS `Patient Name`,
				CASE
					WHEN row_count = 1 THEN t.`mrn`
					ELSE NULL
				END AS `MRN`,
				CASE
					WHEN row_count = 1 THEN t.`status`
					ELSE NULL
				END AS `Status`,
				CASE
					WHEN row_count = 1 THEN t.`insurance_name`
					ELSE NULL
				END AS `Insurance Name`,
				CASE
					WHEN row_count = 1 THEN t.`claim_amount`
					ELSE NULL
				END AS `Claim Amount`,
				CASE
					WHEN row_count = 1 THEN t.`total_settled`
					ELSE NULL
				END AS `Total Settled Amount`,
				CASE
					WHEN row_count = 1 THEN t.`total_tds`
					ELSE NULL
				END AS `Total TDS Amount`,
				CASE
					WHEN row_count = 1 THEN t.`total_disallowance`
					ELSE NULL
				END AS `Total Disallowance Amount`,
				CASE
					WHEN row_count = 1 THEN t.`outstanding_amount`
					ELSE NULL
				END AS `Outstanding Amount`,
				t.entry_type as `Entry Type`,
				t.entry_name as `Entry Name`,
				t.settled_amount as `Settled Amount`,
				t.tds_amount as `TDS Amount`,
				t.disallowed_amount as `Disallowed Amount`,
				t.allocated_amount as `Allocated Amount`,
				t.utr_date as `UTR Date`,
				t.utr_number as `UTR Number`,
				t.payment_posting_date as `Payment Posting Date`,
				t.payment_created_date as `Payment Created Date`,
				t.match_logic as `Match Logic`,
				t.settlement_advice as`Settlement Advice`,
				t.payers_remark as `Payer's Remark`,
				t.`Bank Account` as 'Bank Account',
				t.`Bank Entity` as `Bank Entity`,
				t.`Bank Region` as `Bank Region`,
				t.`Bank Payer` as `Bank Payer`
			FROM 
			(SELECT *, row_number() over ( partition by `vsir`.`bill_number`
			order by
				`vsir`.bill_number) AS `row_count` FROM `veiwSales Invoice Report` vsir WHERE {condition}) t
				ORDER BY
				t.`bill_number`,
				t.row_count"""
    data = frappe.db.sql(query, as_dict=True)
    columns = [
        {'fieldname': 'Bill Number', 'label': 'Bill Number', 'fieldtype': 'Data'},
        {'fieldname': 'Bill Date', 'label': 'Bill Date', 'fieldtype': 'Date'},
        {'fieldname': 'Entity', 'label': 'Entity', 'fieldtype': 'Data'},
        {'fieldname': 'Region', 'label': 'Region', 'fieldtype': 'Data'},
        {'fieldname': 'Branch', 'label': 'Branch', 'fieldtype': 'Data'},
        {'fieldname': 'Branch Type', 'label': 'Branch Type', 'fieldtype': 'Data'},
        {'fieldname': 'Customer', 'label': 'Customer', 'fieldtype': 'Data'},
        {'fieldname': 'Customer Group', 'label': 'Customer Group', 'fieldtype': 'Data'},
        {'fieldname': 'Claim ID', 'label': 'Claim ID', 'fieldtype': 'Data'},
        {'fieldname': 'MA Claim ID', 'label': 'MA Claim ID', 'fieldtype': 'Data'},
        {'fieldname': 'Patient Name', 'label': 'Patient Name', 'fieldtype': 'Data'},
        {'fieldname': 'MRN', 'label': 'MRN', 'fieldtype': 'Data'},
        {'fieldname': 'Status', 'label': 'Status', 'fieldtype': 'Data'},
        {'fieldname': 'Insurance Name', 'label': 'Insurance Name', 'fieldtype': 'Data'},
        {'fieldname': 'Claim Amount', 'label': 'Claim Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'Total Settled Amount', 'label': 'Total Settled Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'Total TDS Amount', 'label': 'Total TDS Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'Total Disallowance Amount', 'label': 'Total Disallowance Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'Outstanding Amount', 'label': 'Outstanding Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'Entry Type', 'label': 'Entry Type', 'fieldtype': 'Data'},
        {'fieldname': 'Entry Name', 'label': 'Entry Name', 'fieldtype': 'Data'},
        {'fieldname': 'Settled Amount', 'label': 'Settled Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'TDS Amount', 'label': 'TDS Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'Disallowed Amount', 'label': 'Disallowed Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'Allocated Amount', 'label': 'Allocated Amount', 'fieldtype': 'Currency'},
        {'fieldname': 'UTR Date', 'label': 'UTR Date', 'fieldtype': 'Date'},
        {'fieldname': 'UTR Number', 'label': 'UTR Number', 'fieldtype': 'Data'},
        {'fieldname': 'Payment Posting Date', 'label': 'Payment Posting Date', 'fieldtype': 'Date'},
        {'fieldname': 'Payment Created Date', 'label': 'Payment Created Date', 'fieldtype': 'Date'},
        {'fieldname': 'Match Logic', 'label': 'Match Logic', 'fieldtype': 'Data'},
        {'fieldname': 'Settlement Advice', 'label': 'Settlement Advice', 'fieldtype': 'Data'},
        {'fieldname': "Payer's Remark", 'label': "Payer's Remark", 'fieldtype': 'Data'},
        {'fieldname': 'Bank Account', 'label': 'Bank Account', 'fieldtype': 'Data'},
        {'fieldname': 'Bank Entity', 'label': 'Bank Entity', 'fieldtype': 'Data'},
        {'fieldname': 'Bank Region', 'label': 'Bank Region', 'fieldtype': 'Data'},
        {'fieldname': 'Bank Payer', 'label': 'Bank Payer', 'fieldtype': 'Data'}]

    return columns, data


def get_condition(filters):
    field_and_condition = {
        'bill_entity': 'vsir.entity IN ',
        'bill_region': 'vsir.region IN ',
        'bill_branch': 'vsir.branch IN ',
        'bill_branch_type': 'vsir.branch_type IN ',
        'bill_customer': 'vsir.customer IN ',
        'bill_customer_group': 'vsir.customer_group IN ',
        'from_bill_date': 'vsir.bill_date <= ',
        'to_bill_date': 'vsir.bill_date >= ',
        'bill_status': 'vsir.status IN ',
        'from_utr_date': 'vsir.utr_date <= ',
        'to_utr_date': 'vsir.utr_date >= ',
        'match_logic': 'vsir.match_logic IN ',
        'bank_account': 'vsir.`Bank Account` IN ',
        'bank_entity': 'vsir.`Bank Entity` IN ',
        'bank_region': 'vsir.`Bank Region` IN ',
        'bank_payer': 'vsir.`Bank Payer` IN'
    }
    conditions = []
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
