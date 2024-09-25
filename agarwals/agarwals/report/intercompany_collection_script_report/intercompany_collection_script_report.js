// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

frappe.query_reports["Intercompany Collection Script Report"] = {
	onload: function (report) { 
		report.page.add_inner_button("Apply Filters", function () { 
			report.set_filter_value('execute', 1); });
		
		report.page.add_inner_button("Remove Filters", function (){
		  report.set_filter_value('execute', 1);
		  report.set_filter_value('from_posting_date',null);
		  report.set_filter_value('to_posting_date',null);
		  report.set_filter_value('bill_branch',[]);
		  report.set_filter_value('bill_entity',[]);
		  report.set_filter_value('bank_entity',[]);
		  report.set_filter_value('bank_account',[]);
		  report.set_filter_value('from_utr_date',null);
		  report.set_filter_value('to_utr_date',null);
		});
	},
		 "filters": 
		 [
			{ "fieldname": "from_posting_date", 
			  "label": __("From Posting Date"), 
			  "fieldtype": "Date", 
			  "on_change": function (report) { report.set_filter_value('execute', 0) 

			  } 
			},
			   { 
				"fieldname": "to_posting_date", 
				"label": __("To Posting Date"), 
				"fieldtype": "Date", 
				"on_change": function (report) { report.set_filter_value('execute', 0) 	
				}
			},
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
					"fieldname": "bank_account",
					"label": __("Bank Account"),
					"fieldtype": "MultiSelectList",
					"options": "Bank Account",
					"get_data": function(txt) {
						return frappe.db.get_link_options('Bank Account', txt);
					},
					"on_change": function (report) { report.set_filter_value('execute', 0) }
				},
				{ "fieldname": "from_utr_date", 
					"label": __("From UTR Date"), 
					"fieldtype": "Date", 
					"on_change": function (report) { report.set_filter_value('execute', 0) 
	  
					} 
				  },
				  { "fieldname": "to_utr_date", 
					"label": __("To UTR Date"), 
					"fieldtype": "Date", 
					"on_change": function (report) { report.set_filter_value('execute', 0) 
	  
					} 
				  }


			] 
			};

