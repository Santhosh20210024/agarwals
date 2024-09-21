import frappe

def execute(filters=None):
    filters = set_region_filter(filters)
    filters = set_region_filter(filters)
    query = """
    SELECT
        CASE
            WHEN row_count = 1 THEN vsir.`Bill Number`
            ELSE NULL
        END AS Bill_Number,
        CASE
            WHEN row_count = 1 THEN vsir.`Bill Date`
            ELSE NULL
        END AS Bill_Date,
        CASE
            WHEN row_count = 1 THEN vsir.`Entity`
            ELSE NULL
        END AS Entity,
        CASE
            WHEN row_count = 1 THEN vsir.`Region`
            ELSE NULL
        END AS Region,
        CASE
            WHEN row_count = 1 THEN vsir.`Branch`
            ELSE NULL
        END AS Branch,
        CASE
            WHEN row_count = 1 THEN vsir.`Branch Type`
            ELSE NULL
        END AS Branch_Type,
        CASE
            WHEN row_count = 1 THEN vsir.`Customer`
            ELSE NULL
        END AS Customer,
        CASE
            WHEN row_count = 1 THEN vsir.`Customer Group`
            ELSE NULL
        END AS Customer_Group,
        CASE
            WHEN row_count = 1 THEN vsir.`Claim ID`
            ELSE NULL
        END AS Claim_ID,
        CASE
            WHEN row_count = 1 THEN vsir.`MA Claim ID`
            ELSE NULL
        END AS MA_Claim_ID,
        CASE
            WHEN row_count = 1 THEN vsir.`Patient Name`
            ELSE NULL
        END AS Patient_Name,
        CASE
            WHEN row_count = 1 THEN vsir.`MRN`
            ELSE NULL
        END AS MRN,
        CASE
            WHEN row_count = 1 THEN vsir.`Status`
            ELSE NULL
        END AS Status,
        CASE
            WHEN row_count = 1 THEN vsir.`Insurance Name`
            ELSE NULL
        END AS Insurance_Name,
        CASE
            WHEN row_count = 1 THEN vsir.`Claim Amount`
            ELSE NULL
        END AS Claim_Amount,
        CASE
            WHEN row_count = 1 THEN vsir.`Total Settled Amount`
            ELSE NULL
        END AS Total_Settled_Amount,
        CASE
            WHEN row_count = 1 THEN vsir.`Total TDS Amount`
            ELSE NULL
        END AS Total_TDS_Amount,
        CASE
            WHEN row_count = 1 THEN vsir.`Total Disallowance Amount`
            ELSE NULL
        END AS Total_Disallowance_Amount,
        CASE
            WHEN row_count = 1 THEN vsir.`Outstanding Amount`
            ELSE NULL
        END AS Outstanding_Amount,
        'OB' as Type
    FROM
        `viewSales Invoice Report 24-25 with Row Number` vsir
    WHERE vsir.`Status` NOT IN ('Paid','Cancelled') and vsir.`Region` IN %(region)s and vsir.`Entity` IN %(entity)s
    GROUP BY vsir.`Bill Number`
    UNION ALL
    SELECT
        CASE
            WHEN row_count = 1 THEN `UTR_Number`
            ELSE NULL
        END AS UTR_Number,
        CASE
            WHEN row_count = 1 THEN `UTR_Date`
            ELSE NULL
        END AS UTR_Date,
        CASE
            WHEN row_count = 1 THEN `Entity`
            ELSE NULL
        END AS Entity,
        CASE
            WHEN row_count = 1 THEN `Region`
            ELSE NULL
        END AS Region,
        CASE
            WHEN row_count = 1 THEN `Bank_Account`
            ELSE NULL
        END AS Bank_Account,
        CASE
            WHEN row_count = 1 THEN `Branch_Type`
            ELSE NULL
        END AS Branch_Type,
        CASE
            WHEN row_count = 1 THEN `Insurance`
            ELSE NULL
        END AS Insurance,
        CASE
            WHEN row_count = 1 THEN `Party_Group`
            ELSE NULL
        END AS Party_Group,
        CASE
            WHEN row_count = 1 THEN `Internal_Id`
            ELSE NULL
        END AS Internal_Id,
        CASE
            WHEN row_count = 1 THEN `Internal_Id`
            ELSE NULL
        END AS Internal_Id1,
        CASE
		   WHEN row_count = 1 THEN `Description`
		   ELSE NULL
	    END AS `Description`,
        NULL AS Unused2,
        CASE
            WHEN row_count = 1 THEN `Status`
            ELSE NULL
        END AS Status,
        NULL as Unused6,
        CASE
            WHEN row_count = 1 THEN -`Current_Deposit`
            ELSE NULL
        END AS Current_Deposit,
        CASE
            WHEN row_count = 1 THEN -`Current_Allocated_Amount`
            ELSE NULL
        END AS Current_Allocated_Amount,
        NULL AS Unused4,
        NULL AS Unused5,
        CASE
            WHEN row_count = 1 THEN -`Current_UnAllocated`
            ELSE NULL
        END AS Current_UnAllocated_Amount,
        'OR' AS Type
    FROM
        `viewSorted Current Brank Transaction` vscbt
    WHERE vscbt.`Status` NOT IN ('Reconciled','Cancelled') and vscbt.`Region`  in %(region)s and vscbt.`Entity` in %(entity)s
    GROUP BY vscbt.`UTR_Number`
    """

    # Execute the query and fetch the data
    data = frappe.db.sql(query, filters, as_dict=True)

    # Define columns to be displayed in the report
    columns = [
        {"label": "Bill Number", "fieldname": "Bill_Number", "fieldtype": "Data"},
        {"label": "Bill Date", "fieldname": "Bill_Date", "fieldtype": "Date"},
        {"label": "Entity", "fieldname": "Entity", "fieldtype": "Data"},
        {"label": "Region", "fieldname": "Region", "fieldtype": "Data"},
        {"label": "Branch", "fieldname": "Branch", "fieldtype": "Data"},
        {"label": "Branch Type", "fieldname": "Branch_Type", "fieldtype": "Data"},
        {"label": "Customer", "fieldname": "Customer", "fieldtype": "Data"},
        {"label": "Customer Group", "fieldname": "Customer_Group", "fieldtype": "Data"},
        {"label": "Claim ID", "fieldname": "Claim_ID", "fieldtype": "Data"},
        {"label": "MA Claim ID", "fieldname": "MA_Claim_ID", "fieldtype": "Data"},
        {"label": "Patient Name", "fieldname": "Patient_Name", "fieldtype": "Data"},
        {"label": "MRN", "fieldname": "MRN", "fieldtype": "Data"},
        {"label": "Status", "fieldname": "Status", "fieldtype": "Data"},
        {"label": "Insurance Name", "fieldname": "Insurance_Name", "fieldtype": "Data"},
        {"label": "Claim Amount", "fieldname": "Claim_Amount", "fieldtype": "Currency"},
        {"label": "Total Settled Amount", "fieldname": "Total_Settled_Amount", "fieldtype": "Currency"},
        {"label": "Total TDS Amount", "fieldname": "Total_TDS_Amount", "fieldtype": "Currency"},
        {"label": "Total Disallowance Amount", "fieldname": "Total_Disallowance_Amount", "fieldtype": "Currency"},
        {"label": "Outstanding Amount", "fieldname": "Outstanding_Amount", "fieldtype": "Currency"},
        {"label": "Type", "fieldname": "Type", "fieldtype": "Data"}
    ]

    return columns, data

def set_region_filter(filters): 
    if filters['region'] :
         filters['region'] = tuple(filters.get('region'))
    else : 
         filters['region']=tuple(frappe.get_all('Region',pluck='name'))   
    return filters

def set_entity_filter(filters):
    if filters['entity'] :
         filters['entity'] = tuple(filters.get('entity'))
    else : 
         filters['entity']=tuple(frappe.get_all('Entity',pluck='name'))   
    return filters