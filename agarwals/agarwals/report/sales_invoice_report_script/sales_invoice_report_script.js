// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Invoice Report Script"] = {
	onload: function(report) {
        report.page.add_inner_button("Apply Filters", function() {
            report.set_filter_value('execute',1);
        });
        report.page.add_inner_button("Clear Filters", function() {
            report.set_filter_value('execute',1)
            report.set_filter_value('bill_entity',[]);
            report.set_filter_value('bill_region',[]);
            report.set_filter_value('bill_branch',[]);
            report.set_filter_value('bill_branch_type',[]);
            report.set_filter_value('bill_customer',[]);
			report.set_filter_value('bill_customer_group',[]);
			report.set_filter_value('from_bill_date',null);
			report.set_filter_value('to_bill_date',null);
			report.set_filter_value('bill_status',[]);
			report.set_filter_value('from_utr_date',null);
			report.set_filter_value('to_utr_date',null);
			report.set_filter_value('match_logic',[]);
			report.set_filter_value('bank_account',[]);
			report.set_filter_value('bank_entity',[]);
			report.set_filter_value('bank_region',[]);
			report.set_filter_value('bank_payer',[]);
        });

    },

	"filters": [
		{
            "fieldname": "bill_entity",
            "label": __("Bill Entity"),
            "fieldtype": "MultiSelectList",
			"options": "Entity",
			"get_data": function (txt){
                return frappe.db.get_link_options('Entity',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bill_region",
            "label": __("Bill Region"),
            "fieldtype": "MultiSelectList",
			"options": "Region",
			"get_data": function (txt){
                return frappe.db.get_link_options('Region',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bill_branch",
            "label": __("Bill Branch"),
            "fieldtype": "MultiSelectList",
			"options": "Branch",
			"get_data": function (txt){
                return frappe.db.get_link_options('Branch',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bill_branch_type",
            "label": __("Bill Branch Type"),
            "fieldtype": "MultiSelectList",
			"options": "Branch Type",
			"get_data": function (txt){
                return frappe.db.get_link_options('Branch Type',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bill_customer",
            "label": __("Bill Customer"),
            "fieldtype": "MultiSelectList",
			"options": "Customer",
			"get_data": function (txt){
                return frappe.db.get_link_options('Customer',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bill_customer_group",
            "label": __("Bill Customer Group"),
            "fieldtype": "MultiSelectList",
			"options": "Customer Group",
			"get_data": function (txt){
                return frappe.db.get_link_options('Customer Group',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
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
		{
            "fieldname": "bill_status",
            "label": __("Bill Status"),
            "fieldtype": "MultiSelectList",
            "options": [{'value':'Paid','description':''},
                {'value':'Unpaid','description':''},
                {'value':'Partly Paid','description':''},
                {'value':'Cancelled','description':''}],
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "from_utr_date",
            "label": __("From UTR Date"),
            "fieldtype": "Date",
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "to_utr_date",
            "label": __("To UTR Date"),
            "fieldtype": "Date",
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "match_logic",
            "label": __("Match Logic"),
            "fieldtype": "MultiSelectList",
			"options": [{'value':'MA5-BN','description':''},
                {'value':'MA1-CN','description':''},
                {'value':'MA3-CN','description':''}],
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bank_account",
            "label": __("Bank Account"),
            "fieldtype": "MultiSelectList",
			"options": "Bank Account",
			"get_data": function (txt){
                return frappe.db.get_link_options('Bank Account',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bank_entity",
            "label": __("Bank Entity"),
            "fieldtype": "MultiSelectList",
			"options": "Entity",
			"get_data": function (txt){
                return frappe.db.get_link_options('Entity',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bank_region",
            "label": __("Bank Region"),
            "fieldtype": "MultiSelectList",
			"options": "Region",
			"get_data": function (txt){
                return frappe.db.get_link_options('Region',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname": "bank_payer",
            "label": __("Bank Payer"),
            "fieldtype": "MultiSelectList",
			"options": "Customer",
			"get_data": function (txt){
                return frappe.db.get_link_options('Customer',txt)
            },
            "on_change": function (report) {
               report.set_filter_value('execute',0)
           }
        },
		{
            "fieldname":"execute",
            "label":__("Execute"),
            "fieldtype":"Check",
            "default": 1,
            "hidden": 1
        }
	]
};
