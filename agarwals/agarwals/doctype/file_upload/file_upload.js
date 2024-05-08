// Added for the Upload Button
var set_css = function () {
  document.querySelectorAll("[data-fieldname='upload']")[1].style.backgroundColor = "#2490EF";
  document.querySelectorAll("[data-fieldname='upload']")[1].style.color = "white";
  document.querySelectorAll("[data-action='delete_rows']")[0].style.display = "None";
  document.querySelector("[data-fieldname='zip_status']").querySelector("[class='control-input-wrapper']").querySelector("[class='control-value like-disabled-input']").style.color="Green"
       
}

// Read Only Validation
const verify_read_only = (frm) => {
  var isOldDocument = frm.doc.__islocal ? 0 : 1;
  frm.set_df_property("upload", "read_only", isOldDocument);
  frm.set_df_property("payer_type", "read_only", isOldDocument);
  frm.set_df_property("bank_account", "read_only", isOldDocument);
  frm.set_df_property("document_type", "read_only", isOldDocument);
  frm.set_df_property("file", "read_only", isOldDocument);
  frm.set_df_property("file_format", "read_only", isOldDocument);
}


function extract_zip(frm) {
  if (frm.doc.status == 'Zip') {
    frm.add_custom_button(__('Extract Zip'), function (frm) {
      if(cur_frm.doc.document_type == 'Claim Book' || cur_frm.doc.document_type == 'Debtors Report'){
        frappe.call({
          method: 'agarwals.agarwals.doctype.file_upload.file_upload.run_extractor',
          args: {
            fid: cur_frm.docname,
            ffield: null
          },
          freeze: true,
          freeze_message: "Files are Extracting....",
          callback: function (r) {
            if (r.message) {
              frappe.msgprint(r.message)
            }
          }
        });
      }
      else{
      let fields = undefined
      if(cur_frm.doc.document_type == 'Settlement Advice'){
        fields = {
          label: 'Payer Name',
          fieldname: 'payer',
          fieldtype: 'Link',
          options: 'Customer',
          description: 'if you want to map all the files with this payer name'
        }
        }
      if(cur_frm.doc.document_type == 'Bank Statement'){
        fields =  {
          label: 'Bank Account',
          fieldname: 'bank_account',
          fieldtype: 'Link',
          options: 'Bank Account',
          description: 'if you want to map all the files with this bank account'
      }
      }
      let extract = new frappe.ui.Dialog({
        'title' : 'Extract Configuration',
        'fields' : [
            fields            
        ],
        primary_action_label: 'Extract',
        primary_action(values) {
          console.log(values)
          let data = null
            if(cur_frm.doc.document_type == 'Settlement Advice' && (typeof(values.payer) != 'undefined')){
                data = values.payer
            }
            else if(cur_frm.doc.document_type == 'Bank Statement' && typeof(values.bank_account) != 'undefined'){
                data = values.bank_account
            }
            else{
                data = null
            }
            frappe.call({
            method: 'agarwals.agarwals.doctype.file_upload.file_upload.run_extractor',
            args: {
              fid: cur_frm.docname,
              ffield: data
            },
            freeze: true,
            freeze_message: "Files are Extracting....",
            callback: function (r) {
              if (r.message) {
                frappe.msgprint(r.message)
              }
            }
          });
          extract.hide()
        }
    })

    extract.show()
    }},  __('Action'));
  }
}

function process_zip(frm) {
  if (frm.doc.status == 'Zip') {
    frm.add_custom_button(__('Process Zip'), function (frm) {
      frappe.confirm(
        'Are you sure you want to perform this action ?',
        function (frm) {
          frappe.call({
            method: 'agarwals.agarwals.doctype.file_upload.file_upload.run_zip_entires',
            args: {
              fid: cur_frm.docname
            },
            freeze: true,
            freeze_message: "Files are uploading....",
            callback: function (r) {
              if (r.message) {
                frappe.msgprint(r.message)
              }
            }
          });
        },
        function () {}
      );
    }, __('Action'));
  }
}

frappe.ui.form.on('File upload', {
  onload: function (frm) {
    extract_zip(frm)
    process_zip(frm)
    verify_read_only(frm)
    set_css()
  },
  refresh: function (frm) {
    extract_zip(frm)
    process_zip(frm)
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