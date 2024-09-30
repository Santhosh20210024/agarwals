// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bill Entry', {
	refresh: function(frm) {
        set_bill_list(frm, frm.doc.bills)
	},
    bills: function (frm){
        set_bill_list(frm, frm.doc.bills)
    },
    bulk_bills: function (frm){
        frm.clear_table('bills');
        let bill_list = frm.doc.bulk_bills.trim().split('\n');
        bill_list.forEach(bill => {
            if(bill !== ''){
                let new_bill = frm.add_child('bills');
                new_bill.bill = bill;
            }}
        )
        set_bill_list(frm,frm.doc.bills)
        frm.refresh_field('bills');
    },
    date: function (frm){
        let input_date = new Date(frm.doc.date)
        let current_date = new Date()
        if(current_date > input_date && Math.trunc((current_date - input_date)/(1000*60*60*24)) > 7){
            frappe.msgprint(__('Back Date More than 7 Days is Not Allowed.'));
            frm.set_value('date',current_date)
        }
        if(input_date > current_date){
            frappe.msgprint(__('Future Date is Not Allowed.'));
            frm.set_value('date',current_date)
        }
    }
});
function set_bill_list(frm, bills_info){
    let bill_list = []
    if(bills_info !== undefined && bills_info.length > 0) {
        bills_info.forEach(bill => {
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Sales Invoice",
                    fields: ["name"],
                    filters: [
                                ["name", "=", bill.bill]
                            ],
                },
                async: false,
                callback: function(r) {
                    if(r.message.length === 0){
                        frappe.throw(bill.bill + " not Found in System")
                    }
                    else{
                        bill_list.push(bill.bill)
                    }
                }
            });
        })
        if(bill_list.length == bills_info.length) {
            frappe.call({
                method: "agarwals.agarwals.doctype.bill_entry.bill_entry.get_bills_info_table",
                args: {
                    'bills': bill_list
                },
                async: false,
                callback: function (r) {
                    if (r.message) {
                        frm.get_field('bill_list').html(r.message);
                    }
                }
            })
        }
        else{
            frm.clear_table('bills');
            frm.refresh_field('bills');
        }
    }
    else{
        frm.get_field('bill_list').html('');
    }
}
