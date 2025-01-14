// Copyright (c) 2023, Agarwals and contributors
// For license information, please see license.txt

 frappe.ui.form.on("Bill", {
 	refresh(frm) {
 	    if(frm.doc.__unsaved !== 1 && frm.doc.verified !== 1){
 	        frm.add_custom_button(__('Verify'),function(){
 	        frm.set_value('verified',1)
 	        frm.save()
 	        frappe.msgprint("Bill has been verified")
 	    })
 	    }
 	},
 });
