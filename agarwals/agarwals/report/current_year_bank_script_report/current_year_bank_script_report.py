import frappe
from datetime import date

def execute(filters=None):
    condition = get_condition(filters)
    if not condition:
        condition = "exists (SELECT 1)"
   
    query = f"""
    SELECT 
        CASE WHEN row_count=1 THEN `Entity` ELSE NULL END AS `Entity`,
        CASE WHEN row_count=1 THEN `Region` ELSE NULL END AS `Region`,
        CASE WHEN row_count=1 THEN `Party_Group` ELSE NULL END AS `Party Group`,
        CASE WHEN row_count=1 THEN `Insurance` ELSE NULL END AS `Insurance`,
        CASE WHEN row_count=1 THEN `UTR_Number` ELSE NULL END AS `UTR Number`,
        CASE WHEN row_count=1 THEN `UTR_Date` ELSE NULL END AS `UTR Date`,
        CASE WHEN row_count=1 THEN `Current_Allocated_Amount` ELSE NULL END AS `Current Allocated Amount`,
        CASE WHEN row_count=1 THEN `Current_UnAllocated` ELSE NULL END AS `Current Un-Allocated Amount`,
        CASE WHEN row_count=1 THEN `Current_Deposit` ELSE NULL END AS `Current Deposit`,
        CASE WHEN row_count=1 THEN `Branch_Type` ELSE NULL END AS `Branch Type`,
        CASE WHEN row_count=1 THEN `Status` ELSE NULL END AS `Status`,
        CASE WHEN row_count=1 THEN `Bank_Account` ELSE NULL END AS `Bank Account`,
        CASE WHEN row_count=1 THEN `Description` ELSE NULL END AS `Description`,
        CASE WHEN row_count=1 THEN `Reference_Number` ELSE NULL END AS `Reference Number`,
        CASE WHEN row_count=1 THEN `Internal_Id` ELSE NULL END AS `Internal Id`,
        CASE WHEN row_count=1 THEN `Based_On` ELSE NULL END AS `Based On`,
        `Allocated_Amount(Payment_Entries)` AS `Allocated_Amount(Payment_Entries)`,
        `Payment_Document(Payment_Entries)` AS `Payment_Document(Payment_Entries)`,
        `Bill_Region(Payment_Entries)` AS `Bill_Region(Payment_Entries)`,
        `Creation_Date(Payment_Entries)` AS `Creation_Date(Payment_Entries)`,
        `Posting_Date(Payment_Entries)`AS `Posting_Date(Payment_Entries)`,
        `Bill_Date(Payment_Entries)` AS `Bill_Date(Payment_Entries)`,
        `Bill_Branch(Payment_Entries)` AS `Bill_Branch(Payment_Entries)`,
        `Bill_Entity(Payment_Entries)` AS `Bill_Entity(Payment_Entries)`,
        `Bill_Branch_Type(Payment_Entries)` AS `Bill_Branch_Type(Payment_Entries)`,
        `Payment_Entry(Payment_Entries)` AS `Payment_Entry(Payment_Entries)`
    FROM `viewSorted Current Brank Transaction` vscbt
    WHERE {condition}
    """

    if filters.get("execute") == 1:
        print(query)
        data = frappe.db.sql(query, as_dict=True)

    else:
        data = {}

    columns = [
        {"label": "Entity", "fieldname": "Entity", "fieldtype": "Data"},
        {"label": "Region", "fieldname": "Region", "fieldtype": "Data"},
        {"label": "Party Group", "fieldname": "Party Group", "fieldtype": "Data"},
        {"label": "Insurance", "fieldname": "Insurance", "fieldtype": "Data"},
        {"label": "UTR Number", "fieldname": "UTR Number", "fieldtype": "Data"},
        {"label": "UTR Date", "fieldname": "UTR Date", "fieldtype": "Date"},
        {"label": "Current Allocated Amount", "fieldname": "Current Allocated Amount", "fieldtype": "Currency"},
        {"label": "Current Un-Allocated Amount", "fieldname": "Current Un-Allocated Amount", "fieldtype": "Currency"},
        {"label": "Current Deposit", "fieldname": "Current Deposit", "fieldtype": "Currency"},
        {"label": "Branch Type", "fieldname": "Branch Type", "fieldtype": "Data"},
        {"label": "Status", "fieldname": "Status", "fieldtype": "Data"},
        {"label": "Bank Account", "fieldname": "Bank Account", "fieldtype": "Data"},
        {"label": "Description", "fieldname": "Description", "fieldtype": "Data"},
        {"label": "Reference Number", "fieldname": "Reference Number", "fieldtype": "Data"},
        {"label": "Internal Id", "fieldname": "Internal Id", "fieldtype": "Data"},
        {"label": "Based On", "fieldname": "Based On", "fieldtype": "Data"},
        {"label": "Allocated Amount (Payment Entries)", "fieldname": "Allocated_Amount(Payment_Entries)", "fieldtype": "Currency"},
        {"label": "Payment Document (Payment Entries)", "fieldname": "Payment_Document(Payment_Entries)", "fieldtype": "Data"},
        {"label": "Bill Region (Payment Entries)", "fieldname": "Bill_Region(Payment_Entries)", "fieldtype": "Data"},
        {"label": "Creation Date (Payment Entries)", "fieldname": "Creation_Date(Payment_Entries)", "fieldtype": "Date"},
        {"label": "Posting Date (Payment Entries)", "fieldname": "Posting_Date(Payment_Entries)", "fieldtype": "Date"},
        {"label": "Bill Date (Payment Entries)", "fieldname": "Bill_Date(Payment_Entries)", "fieldtype": "Date"},
        {"label": "Bill Branch (Payment Entries)", "fieldname": "Bill_Branch(Payment_Entries)", "fieldtype": "Data"},
        {"label": "Bill Entity (Payment Entries)", "fieldname": "Bill_Entity(Payment_Entries)", "fieldtype": "Data"},
        {"label": "Bill Branch Type (Payment Entries)", "fieldname": "Bill_Branch_Type(Payment_Entries)", "fieldtype": "Data"},
        {"label": "Payment Entry (Payment Entries)", "fieldname": "Payment_Entry(Payment_Entries)", "fieldtype": "Data"}
    ]

    return columns, data

def datetime_converter(o):
    if isinstance(o, date):
        return o.isoformat()


def get_condition(filters):
    field_and_condition = {'from_utr_date':'`UTR Date` >= ','to_utr_date':'`UTR Date <= ','entity':'`Entity` in ', '`Region`':'`Region` in ', 'bank_account':'`Bank Account` in ','status':'`Status` IN ','party_group':'`Party Group` IN '}
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
