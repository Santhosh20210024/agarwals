// Added for the Upload Button
var set_css = function (){ 
  document.querySelectorAll("[data-fieldname='upload']")[1].style.backgroundColor ="#2490EF";
  document.querySelectorAll("[data-fieldname='upload']")[1].style.color ="white"; 
}

// Read Only Validation
const verify_read_only = (frm) => { 
  var isOldDocument = frm.doc.__islocal ? 0 : 1;
  frm.set_df_property("upload", "read_only", isOldDocument);
  frm.set_df_property("payer_type", "read_only", isOldDocument);
  frm.set_df_property("bank_account", "read_only", isOldDocument);
  frm.set_df_property("document_type", "read_only", isOldDocument);
  frm.set_df_property("file", "read_only", isOldDocument);
  frm.set_df_property("file_format", isOldDocument);
}

// Check if the document is old
frappe.ui.form.on('File upload', {
	onload: function(frm) {
          verify_read_only(frm)
          set_css()
          },
  refresh: function(frm) {
          verify_read_only(frm)
          set_css()
  }
});

// private button 
var style = document.createElement('style'); 
style.textContent = `
  .btn.btn-secondary.btn-sm.btn-modal-secondary {
    display: none;
  }
  .flex.config-area {
    display: none;
}`;
document.head.appendChild(style);