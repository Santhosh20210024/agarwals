// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excess Paid - Script"] = {
	onload: function(report) {
        report.page.add_inner_button("Apply Filters", function() {
            report.set_filter_value('execute',1);
        });
        report.page.add_inner_button("Clear Filters", function() {
            report.set_filter_value('execute',1)
            report.set_filter_value('from_bill_date',null);
            report.set_filter_value('to_bill_date',null);
            report.set_filter_value('bill_region',[]);
            report.set_filter_value('bill_entity',[]);
            report.set_filter_value('bill_branch',[]);
        });

    },

	"filters": [
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
            "fieldname": "from_bill_date",
            "label": __("From Bill Date"),
            "fieldtype": "Date",
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
        {
            "fieldname": "to_bill_date",
            "label": __("To Bill Date"),
            "fieldtype": "Date",
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
	]
};
