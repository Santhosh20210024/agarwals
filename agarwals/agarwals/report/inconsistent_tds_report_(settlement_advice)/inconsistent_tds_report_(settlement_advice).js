// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Inconsistent TDS Report (Settlement Advice)"] = {
	onload: function (report) { 
		report.page.add_inner_button("Apply Filters", function () { 
			report.set_filter_value('execute', 1); });

		report.page.add_inner_button("Remove Filters", function (){
		  report.set_filter_value('execute', 1);
		  report.set_filter_value('status',[]);
		  report.set_filter_value('from_paid_date',null);
		  report.set_filter_value('to_paid_date',null);
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
					"fieldname": "status", 
					   "label": __("Status"), 
					   "fieldtype": "MultiSelectList", 
					   "options": [{'value':'Fully Processed','description':''},{'value':'Partially Processed','description':''},{'value':'Warning','description':''},{'value':'Unmatched','description':''},{'value':'Error','description':''}],
					   "on_change": function (report) { report.set_filter_value('execute', 0) }
				   },
				   { "fieldname": "from_paid_date", 
					"label": __("From Paid Date"), 
					"fieldtype": "Date", 
					"on_change": function (report) { report.set_filter_value('execute', 0) 

					} 
				  },
				  { "fieldname": "to_paid_date", 
					"label": __("To Paid Date"), 
					"fieldtype": "Date", 
					"on_change": function (report) { report.set_filter_value('execute', 0) 
					} 
				  }
				
			] 
};
