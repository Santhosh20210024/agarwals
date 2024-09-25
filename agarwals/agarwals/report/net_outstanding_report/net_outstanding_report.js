// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Net Outstanding Report"] = {
	onload: function (report) { 
		report.page.add_inner_button("Apply Filters", function () { 
			report.set_filter_value('execute', 1); });

		report.page.add_inner_button("Remove Filters", function (){
		  report.set_filter_value('execute', 1);
		  report.set_filter_value('branch',[]);
		  report.set_filter_value('entity',[]);
		  report.set_filter_value('party_group',[]);
		  report.set_filter_value('bank_account',[]);
		  report.set_filter_value('status',[]);
		  report.set_filter_value('from_utr_date',null);
		  report.set_filter_value('to_utr_date',null);
		});
	},
		 "filters": 
		 [
				{
					"fieldname": "execute", 
					"label": __("Execute"), 
					"fieldtype": "Check", 
					"default": 1 ,
					"hidden": 1
				},
				{
					"fieldname": "entity",
					"label": __("Entity"),
					"fieldtype": "MultiSelectList",
					"options": "Entity",
					"get_data": function(txt) {
						return frappe.db.get_link_options('Entity', txt);
					},
					"on_change": function (report) { report.set_filter_value('execute', 0) }
				},
			{
				"fieldname": "region",
				"label": __("Region"),
				"fieldtype": "MultiSelectList",
				"options": "Region",
				"get_data": function(txt) {
					return frappe.db.get_link_options('Region', txt);
				},
				"on_change": function (report) { report.set_filter_value('execute', 0) }
			}
			] 
};
