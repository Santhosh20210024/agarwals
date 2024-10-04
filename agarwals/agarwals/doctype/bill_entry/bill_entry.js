// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bill Entry', {
    event_date: function (frm){
        let input_date = new Date(frm.doc.event_date)
        let current_date = new Date()
        if(current_date > input_date && Math.trunc((current_date - input_date)/(1000*60*60*24)) > 7){
            frappe.msgprint(__('Back Date More than 7 Days is Not Allowed.'));
            frm.set_value('event_date',current_date)
        }
        if(input_date > current_date){
            frappe.msgprint(__('Future Date is Not Allowed.'));
            frm.set_value('event_date',current_date)
        }
    }
});