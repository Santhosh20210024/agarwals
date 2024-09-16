import frappe

def execute(filters=None):
    if filters['region'] :
         filters['region'] = tuple(filters.get('region'))
    else : 
         filters['region']=tuple(frappe.get_all('Region',pluck='name'))  
    if not filters.get('from_date'):   
        filters['from_date'] = '2001-01-01'
    if not filters.get('to_date'):
        filters['to_date'] = frappe.utils.today()
    query = """
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
    WHERE vsir.`UTR_Date`>= %(from_date)s and vsir.`UTR_Date`<= %(to_date)s and vsir.`Region` IN %(region)s;
    """

    data = frappe.db.sql(query, filters,as_dict=True)

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
