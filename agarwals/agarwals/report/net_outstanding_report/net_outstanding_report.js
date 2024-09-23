// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Net Outstanding Report"] = {
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
			"fieldname": "entity",
			"label": __("Entity"),
			"fieldtype": "MultiSelectList",
			"options": "Entity",
			"get_data": function(txt) {
				return frappe.db.get_link_options('Entity', txt);
			}
		}
	]
};
