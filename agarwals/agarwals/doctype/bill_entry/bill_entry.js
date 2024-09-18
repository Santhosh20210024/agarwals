// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bill Entry', {
	refresh: function(frm) {
        set_bill_list(frm, frm.doc.bills)
	},
    bills: function (frm){
        set_bill_list(frm, frm.doc.bills)
    }
});
function set_bill_list(frm, bills_info){
    let bill_list = []
    console.log("PRINT1",bills_info)
    if(bills_info !== undefined && bills_info.length > 0) {
        bills_info.forEach(bill => {
            bill_list.push(bill.bill)
        })
        frappe.call({
            method: "agarwals.agarwals.doctype.bill_entry.bill_entry.get_bills_info_table",
            args: {
                'bills':bill_list
            },
            async: false,
            callback: function(r){
                if (r.message){
                    frm.get_field('bill_list').html(r.message);
                }
            }
        })
    }
    else{
        frm.get_field('bill_list').html('');
    }
}
