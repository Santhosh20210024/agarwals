// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Current Year Bank Script Report"] = {
	"filters": [
        {
            "fieldname": "region",
            "label": __("Region"),
            "fieldtype": "MultiSelectList",
            "options": "Region",
            "get_data": function(txt) {
                return frappe.db.get_link_options('Region', txt);
            }
        },
        {
            "fieldname": "from_date",
            "label": __("From UTR Date"),
            "fieldtype": "Date",	
        },
        {
            "fieldname": "to_date",
            "label": __("To UTR Date"),
            "fieldtype": "Date",
        }
    ],
};
