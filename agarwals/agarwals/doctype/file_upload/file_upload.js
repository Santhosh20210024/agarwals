// Copyright (c) 2023, Agarwals and contributors
// For license information, please see license.txt


// Read only
frappe.ui.form.on('File upload', {
	onload: function(frm) {
    frappe.realtime.on("Errorbox", function(response) {
      if (response === "error") {
        frm.set_df_property("upload", "read_only",0);
        frm.set_df_property("payer_type", "read_only",0);
        frm.set_df_property("bank_account", "read_only",0);
        frm.set_df_property("document_type", "read_only",0);
      }
      else{
        frm.set_df_property("upload", "read_only",1);
        frm.set_df_property("payer_type", "read_only",1);
        frm.set_df_property("bank_account", "read_only",1);
        frm.set_df_property("document_type", "read_only",1);
      }
    });    

	 }
});
frappe.ui.form.on('File upload', {
	refresh: function(frm) {
    if (frm.doc.upload != null){
      frm.set_df_property("upload", "read_only",1);
      frm.set_df_property("payer_type", "read_only",1);
      frm.set_df_property("bank_account", "read_only",1);
      frm.set_df_property("document_type", "read_only",1);
    }
    frappe.realtime.on("Errorbox", function(response) {
      if (response === "error") {
        frm.set_df_property("upload", "read_only",0);
        frm.set_df_property("payer_type", "read_only",0);
        frm.set_df_property("bank_account", "read_only",0);
        frm.set_df_property("document_type", "read_only",0);
      }
      else{
        frm.set_df_property("upload", "read_only",1);
        frm.set_df_property("payer_type", "read_only",1);
        frm.set_df_property("bank_account", "read_only",1);
        frm.set_df_property("document_type", "read_only",1);
      }
    });    

	 }
});

// upload button
frappe.ui.form.on('File upload', {
	refresh: function (frm) {
		set_css(frm)
    },
	reload: function (frm) {
		set_css(frm)
    }
});

var set_css = function (frm){
    document.querySelectorAll("[data-fieldname='upload']")[1].style.backgroundColor ="#2490EF";
    document.querySelectorAll("[data-fieldname='upload']")[1].style.color ="white"; 
}

// private button 
var style = document.createElement('style');
style.textContent = `
  .btn.btn-secondary.btn-sm.btn-modal-secondary {
    display: none;
  }
  .flex.config-area {
    display: none;
}
`;

document.head.appendChild(style);

