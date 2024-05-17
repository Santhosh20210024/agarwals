// Copyright (c) 2023, Agarwals and contributors
// For license information, please see license.txt


// Read only
frappe.ui.form.on('File upload', {
	onload: function(frm) {
          // Check if the document is old
          var isOldDocument = frm.doc.__islocal ? 0 : 1;
          // Set the read-only property of the field based on the condition
          frm.set_df_property("upload", "read_only", isOldDocument);
          frm.set_df_property("payer_type", "read_only", isOldDocument);
          frm.set_df_property("bank_account", "read_only", isOldDocument);
          frm.set_df_property("document_type", "read_only", isOldDocument);
      }
  });
  
frappe.ui.form.on('File upload', {
	refresh: function(frm) {
           // Check if the document is old
           var isOldDocument = frm.doc.__islocal ? 0 : 1;
           // Set the read-only property of the field based on the condition
           frm.set_df_property("upload", "read_only", isOldDocument);
           frm.set_df_property("payer_type", "read_only", isOldDocument);
           frm.set_df_property("bank_account", "read_only", isOldDocument);
           frm.set_df_property("document_type", "read_only", isOldDocument);
	 }
});

//date validation
// frappe.ui.form.on('File upload', {
//     date:function(frm){
//         frappe.call({
//             method:"agarwals.agarwals.doctype.fileupload.fileupload.date_validation",
//             args:{
//                 writeback_date : frm.doc.date
//             }
//         })
//     }
// })
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