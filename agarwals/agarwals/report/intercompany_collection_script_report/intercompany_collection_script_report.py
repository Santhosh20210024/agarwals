import frappe

def execute(filters=None):
    query = """``
    SELECT
        COALESCE(table2.BRANCH, "TOTAL") AS "BRANCH",
        table2.branch_entity AS "BRANCH ENTITY",
        table2.bank_entity AS "BANK ENTITY",
        table2.bill_no AS "BILL NO",
        table2.bank_account AS "BANK ACCOUNT",
        table2.utr_number AS "UTR NUMBER",
        table2.narration AS "NARRATION",
        table2.utr_date AS "UTR DATE",
        table2.party_name AS "PARTY",
        table2.posting_date AS "POSTING DATE",
        COALESCE(ROUND(SUM(table2.Amount_recieved_in_AHC_bank_account)), 0) AS "AHCL",
        COALESCE(ROUND(SUM(table2.Amount_recieved_in_AEH_bank_account)), 0) AS "AEHL",
        COALESCE(ROUND(SUM(table2.Amount_recieved_in_AJE_bank_account)), 0) AS "AJE",
        COALESCE(ROUND(SUM(table2.Amount_recieved_in_AEH_bank_account)), 0) + COALESCE(ROUND(SUM(table2.Amount_recieved_in_AHC_bank_account)), 0) + COALESCE(ROUND(SUM(table2.Amount_recieved_in_AJE_bank_account)), 0) AS "TOTAL COLLECTION"
    FROM (
        SELECT
            table1.branch AS BRANCH,
            table1.branch_entity AS branch_entity,
            table1.bank_entity AS bank_entity,
            table1.bill_no AS bill_no,
            table1.bank_account AS bank_account,
            table1.party_name AS party_name,
            table1.utr_number AS utr_number,
            table1.narration AS narration,
            table1.posting_date AS posting_date,
            table1.utr_date AS utr_date,
            CASE WHEN table1.bank_entity = 'AHC' THEN table1.settled_amount END AS Amount_recieved_in_AHC_bank_account,
            CASE WHEN table1.bank_entity = 'AEH' THEN table1.settled_amount END AS Amount_recieved_in_AEH_bank_account,
            CASE WHEN table1.bank_entity = 'AJE' THEN table1.settled_amount END AS Amount_recieved_in_AJE_bank_account
        FROM (
            SELECT
                t.branch,
                t.branch_entity AS branch_entity,
                tbt.custom_entity AS bank_entity,
                t.bill_no AS bill_no,
                tbt.bank_account AS bank_account,
                t.party_name AS party_name,
                tbt.reference_number AS utr_number,
                tbt.description AS narration,
                tbt.date AS utr_date,
                t.posting_date as posting_date,
                t.settled_amount
            FROM `tabBank Transaction` tbt
            JOIN (
                SELECT
                    tpa.branch AS branch,
                    tpa.entity AS branch_entity,
                    tpa.reference_no AS utr_number,
                    SUM(tpa.paid_amount) AS settled_amount,
                    tpa.party_name AS party_name,
                    tpa.custom_sales_invoice As bill_no,
                    tpa.posting_date AS posting_date
                    FROM `tabPayment Entry` tpa
                    Where tpa.status != 'Cancelled' GROUP BY tpa.branch, tpa.reference_no
            ) t ON t.utr_number = tbt.reference_number
        ) table1
    ) table2
    JOIN `tabBranch` tbr ON tbr.name = table2.BRANCH
    GROUP BY table2.branch,table2.bank_account,table2.party_name, table2.utr_number;
    """

    data = frappe.db.sql(query, as_dict=True)

    columns = [
        {"label": "Branch", "fieldname": "BRANCH", "fieldtype": "Data"},
        {"label": "Branch Entity", "fieldname": "BRANCH ENTITY", "fieldtype": "Data"},
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
        {"label": "Total Collection", "fieldname": "TOTAL COLLECTION", "fieldtype": "Currency"}
    ]

    return columns, data
