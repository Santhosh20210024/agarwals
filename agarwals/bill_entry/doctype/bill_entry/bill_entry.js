// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bill Entry', {
	refresh: function(frm) {
        let indicator = document.getElementsByClassName("indicator-pill");
        for (let i = 0; i < indicator.length; i++) {
            indicator[i].style.visibility = "hidden";
        }
        frm.set_value('bill',null)
        frm.set_value('ma_claim_id',null)
        frm.set_value('event',null)
        frm.set_value('date', new Date())
        frm.set_value('mode_of_submission',null)
        frm.set_value('remark',null)
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
