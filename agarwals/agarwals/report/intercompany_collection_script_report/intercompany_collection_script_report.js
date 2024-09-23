// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Intercompany Collection Script Report"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": __("From Posting Date"),
            "fieldtype": "Date",	
        },
        {
            "fieldname": "to_date",
            "label": __("To Posting Date"),
            "fieldtype": "Date",
        }
	]
};
