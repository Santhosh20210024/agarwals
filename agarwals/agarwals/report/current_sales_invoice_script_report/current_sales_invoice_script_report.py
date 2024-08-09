import frappe

def execute(filters=None):
    query = """
    SELECT 
        CASE WHEN row_count=1 THEN vsir.`Bill Number` ELSE NULL END AS `Bill Number`,
        CASE WHEN row_count=1 THEN vsir.`Bill Date` ELSE NULL END AS `Bill Date`,
        CASE WHEN row_count=1 THEN vsir.`Entity` ELSE NULL END AS `Entity`,
        CASE WHEN row_count=1 THEN vsir.`Region` ELSE NULL END AS `Region`,
        CASE WHEN row_count=1 THEN vsir.`Branch` ELSE NULL END AS `Branch`,
        CASE WHEN row_count=1 THEN vsir.`Branch Type` ELSE NULL END AS `Branch Type`,
        CASE WHEN row_count=1 THEN vsir.`Customer` ELSE NULL END AS `Customer`,
        CASE WHEN row_count=1 THEN vsir.`Customer Group` ELSE NULL END AS `Customer Group`,
        CASE WHEN row_count=1 THEN vsir.`Claim ID` ELSE NULL END AS `Claim ID`,
        CASE WHEN row_count=1 THEN vsir.`MA Claim ID` ELSE NULL END AS `MA Claim ID`,
        CASE WHEN row_count=1 THEN vsir.`Patient Name` ELSE NULL END AS `Patient Name`,
        CASE WHEN row_count=1 THEN vsir.`MRN` ELSE NULL END AS `MRN`,
        CASE WHEN row_count=1 THEN vsir.`Status` ELSE NULL END AS `Status`,
        CASE WHEN row_count=1 THEN vsir.`Insurance Name` ELSE NULL END AS `Insurance Name`,
        CASE WHEN row_count=1 THEN vsir.`Claim Amount` ELSE NULL END AS `Claim Amount`,
        CASE WHEN row_count=1 THEN vsir.`Total Settled Amount` ELSE NULL END AS `Total Settled Amount`,
        CASE WHEN row_count=1 THEN vsir.`Total TDS Amount` ELSE NULL END AS `Total TDS Amount`,
        CASE WHEN row_count=1 THEN vsir.`Total Disallowance Amount` ELSE NULL END AS `Total Disallowance Amount`,
        CASE WHEN row_count=1 THEN vsir.`Outstanding Amount` ELSE NULL END AS `Outstanding Amount`,
        vsir.`Entry Type`,
        vsir.`Entry Name`,
        vsir.`Settled Amount`,
        vsir.`TDS Amount`,
        vsir.`Disallowed Amount`,
        vsir.`Allocated Amount`,
        vsir.`UTR Date`,
        vsir.`UTR Number`,
        vsir.`Payment Posting Date`,
        vsir.`Payment Created Date`,
        vsir.`Match Logic`,
        vsir.`Settlement Advice`,
        tsa.payers_remark AS `Payer's Remark`,
        tbt.bank_account as 'Bank Account', 
        tbt.custom_entity as `Bank Entity`,
        tbt.custom_region as `Bank Region`, 
        tbt.party as `Bank Payer`
    FROM `viewSales Invoice Report 24-25 with Row Number` vsir
    LEFT JOIN `tabBank Transaction` tbt ON vsir.`UTR Number` = tbt.name
    LEFT JOIN `tabSettlement Advice` tsa on tsa.name = vsir.`Settlement Advice`;
    """

    data = frappe.db.sql(query, as_dict=True)

    columns = [
        {"label": "Bill Number", "fieldname": "Bill Number", "fieldtype": "Data"},
        {"label": "Bill Date", "fieldname": "Bill Date", "fieldtype": "Date"},
        {"label": "Entity", "fieldname": "Entity", "fieldtype": "Data"},
        {"label": "Region", "fieldname": "Region", "fieldtype": "Data"},
        {"label": "Branch", "fieldname": "Branch", "fieldtype": "Data"},
        {"label": "Branch Type", "fieldname": "Branch Type", "fieldtype": "Data"},
        {"label": "Customer", "fieldname": "Customer", "fieldtype": "Data"},
        {"label": "Customer Group", "fieldname": "Customer Group", "fieldtype": "Data"},
        {"label": "Claim ID", "fieldname": "Claim ID", "fieldtype": "Data"},
        {"label": "MA Claim ID", "fieldname": "MA Claim ID", "fieldtype": "Data"},
        {"label": "Patient Name", "fieldname": "Patient Name", "fieldtype": "Data"},
        {"label": "MRN", "fieldname": "MRN", "fieldtype": "Data"},
        {"label": "Status", "fieldname": "Status", "fieldtype": "Data"},
        {"label": "Insurance Name", "fieldname": "Insurance Name", "fieldtype": "Data"},
        {"label": "Claim Amount", "fieldname": "Claim Amount", "fieldtype": "Currency"},
        {"label": "Total Settled Amount", "fieldname": "Total Settled Amount", "fieldtype": "Currency"},
        {"label": "Total TDS Amount", "fieldname": "Total TDS Amount", "fieldtype": "Currency"},
        {"label": "Total Disallowance Amount", "fieldname": "Total Disallowance Amount", "fieldtype": "Currency"},
        {"label": "Outstanding Amount", "fieldname": "Outstanding Amount", "fieldtype": "Currency"},
        {"label": "Entry Type", "fieldname": "Entry Type", "fieldtype": "Data"},
        {"label": "Entry Name", "fieldname": "Entry Name", "fieldtype": "Data"},
        {"label": "Settled Amount", "fieldname": "Settled Amount", "fieldtype": "Currency"},
        {"label": "TDS Amount", "fieldname": "TDS Amount", "fieldtype": "Currency"},
        {"label": "Disallowed Amount", "fieldname": "Disallowed Amount", "fieldtype": "Currency"},
        {"label": "Allocated Amount", "fieldname": "Allocated Amount", "fieldtype": "Currency"},
        {"label": "UTR Date", "fieldname": "UTR Date", "fieldtype": "Date"},
        {"label": "UTR Number", "fieldname": "UTR Number", "fieldtype": "Data"},
        {"label": "Payment Posting Date", "fieldname": "Payment Posting Date", "fieldtype": "Date"},
        {"label": "Payment Created Date", "fieldname": "Payment Created Date", "fieldtype": "Date"},
        {"label": "Match Logic", "fieldname": "Match Logic", "fieldtype": "Data"},
        {"label": "Settlement Advice", "fieldname": "Settlement Advice", "fieldtype": "Data"},
        {"label": "Payer's Remark", "fieldname": "Payer's Remark", "fieldtype": "Data"},
        {"label": "Bank Account", "fieldname": "Bank Account", "fieldtype": "Data"},
        {"label": "Bank Entity", "fieldname": "Bank Entity", "fieldtype": "Data"},
        {"label": "Bank Region", "fieldname": "Bank Region", "fieldtype": "Data"},
        {"label": "Bank Payer", "fieldname": "Bank Payer", "fieldtype": "Data"}
    ]

    return columns, data
