// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["OB Available - OR Not Available Script Report"] = {
	onload: function (report) { 
		report.page.add_inner_button("Apply Filters", function () { 
			report.set_filter_value('execute', 1); });

		report.page.add_inner_button("Remove Filters", function (){
		  report.set_filter_value('execute', 1);
		  report.set_filter_value('bill_branch',[]);
		  report.set_filter_value('bill_entity',[]);
		  report.set_filter_value('bill_region',[]);
		  report.set_filter_value('bank_entity',[]);
		  report.set_filter_value('bank_region',[]);
		  report.set_filter_value('bank_account',[]);
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
					"fieldname": "bill_entity",
					"label": __(" Bill Entity"),
					"fieldtype": "MultiSelectList",
					"options": "Entity",
					"get_data": function(txt) {
						return frappe.db.get_link_options('Entity', txt);
					},
					"on_change": function (report) { report.set_filter_value('execute', 0) }
				},
				{
					"fieldname": "bill_region",
					"label": __("Bill Region"),
					"fieldtype": "MultiSelectList",
					"options": "Region",
					"get_data": function(txt) {
						return frappe.db.get_link_options('Region', txt);
					},
					"on_change": function (report) { report.set_filter_value('execute', 0) }
				},
				{
					"fieldname": "bill_branch",
					"label": __("Bill Branch"),
					"fieldtype": "MultiSelectList",
					"options": "Branch",
					"get_data": function(txt) {
						return frappe.db.get_link_options('Branch', txt);
					},
					"on_change": function (report) { report.set_filter_value('execute', 0) }
				},
				{
					"fieldname": "bank_entity",
					"label": __("Bank Entity"),
					"fieldtype": "MultiSelectList",
					"options": "Entity",
					"get_data": function(txt) {
						return frappe.db.get_link_options('Entity', txt);
					},
					"on_change": function (report) { report.set_filter_value('execute', 0) }
				},
				{
					"fieldname": "bank_region",
					"label": __("Bank Region"),
					"fieldtype": "MultiSelectList",
					"options": "Region",
					"get_data": function(txt) {
						return frappe.db.get_link_options('Region', txt);
					},
					"on_change": function (report) { report.set_filter_value('execute', 0) }
				},
				{
					"fieldname": "bank_account",
					"label": __("Bank Account"),
					"fieldtype": "MultiSelectList",
					"options": "Bank Account",
					"get_data": function(txt) {
						return frappe.db.get_link_options('Bank Account', txt);
					},
					"on_change": function (report) { report.set_filter_value('execute', 0) }
				}


			] 
};