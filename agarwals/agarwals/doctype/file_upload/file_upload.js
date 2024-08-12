var set_css = function () {
  document.querySelectorAll("[data-fieldname='download_template']")[1].style.backgroundColor = "#2490EF";
  document.querySelectorAll("[data-fieldname='download_template']")[1].style.color = "white";
  document.querySelectorAll("[data-fieldname='upload']")[1].style.backgroundColor = "#2490EF";
  document.querySelectorAll("[data-fieldname='upload']")[1].style.color = "white";
  document.querySelectorAll("[data-action='delete_rows']")[0].style.display = "None";
}

// Color Changing Property
var change_zip_status_color = function () {
  const code = document.querySelector("[data-fieldname='zip_status']")
    .querySelector("[class='control-input-wrapper']")
    .querySelector("[class='control-value like-disabled-input']")

  var status = code.innerHTML
  if (status == "Processed" || status == "Processing") {
    code.style.color = "Green"
  }
  else if (status == "Extracted" || status == "Extracting") {
    code.style.color = "Red"
  }
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

function process() {
  frappe.confirm(
    'Are you sure you want to perform this action ?',
    function () {
      frappe.call({
        method: 'agarwals.agarwals.doctype.file_upload.file_upload.process_zip_entires',
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
    })
}

function extract() {
  let data = null
  if(cur_frm.doc.file_format == 'ZIP'){
    if(cur_frm.doc.document_type == 'Settlement Advice'){
      data = cur_frm.doc.payer_type
    }
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
}

frappe.ui.form.on('File upload', {
  extract: function (frm) {
    extract(frm);
  },
  process: function (frm) {
    process(frm);
  }
});

frappe.ui.form.on('File upload', {
  onload: function (frm) {
    verify_read_only(frm)
    set_css()
  },
  refresh: function (frm) {
    change_zip_status_color()
    update_payer_button(frm)
    verify_read_only(frm)
    set_css()
  }
});

function update_payer_button(frm) {
  var updateButtonClass = 'update-payer-button'

  function createButton() {
    var addButton = document.createElement('button');
    addButton.innerText = 'Update';
    addButton.className = `btn btn-xs btn-secondary grid-add-row ${updateButtonClass}`;

    addButton.addEventListener('click', function () {
      update_payer(frm);
    });
    return addButton;
  }

  if (frm.doc.document_type == "Bank Statement") {
    var gridButtons = frm.fields_dict['mapping_bank'].grid.wrapper.find('.grid-buttons');

    // Check if the button is already added
    if (!gridButtons.find(`.${updateButtonClass}`).length) {
      gridButtons.append(createButton());
    }
  }

  if (frm.doc.document_type == "Settlement Advice") {
    var gridButtons = frm.fields_dict['mapping_advice'].grid.wrapper.find('.grid-buttons');

    // Check if the button is already added
    if (!gridButtons.find(`.${updateButtonClass}`).length) {
      gridButtons.append(createButton());
    }
  }
}

var style = document.createElement('style');
style.textContent = `
  .btn.btn-secondary.btn-sm.btn-modal-secondary {
    display: none;
  }
  .flex.config-area {
    display: none;
}`;
document.head.appendChild(style);

function update_payer(frm) {
  if (frm.doc.document_type == "Settlement Advice") {
    const child_rows = frm.get_selected()
    if (Object.keys(child_rows).length > 0) {
      let d = new frappe.ui.Dialog({
        title: 'Payer details',
        fields: [
          {
            label: 'Payer',
            fieldname: 'payer',
            fieldtype: 'Link',
            options: 'Customer'
          }
        ],
        size: 'small',
        primary_action_label: 'Submit',
        primary_action(values) {

          var child_row = child_rows.mapping_advice
          for (var i = 0; i < child_row.length; i++) {
            frappe.model.set_value("Settlement Advice Mapping", child_row[i], "payer_name", values.payer)
            frm.refresh_field("mapping_advice")
          }
          d.hide();
        }
      });
      d.show();
    }
  }

  if (frm.doc.document_type == "Bank Statement") {
    const child_rows = frm.get_selected()
    if (Object.keys(child_rows).length > 0) {
      let d = new frappe.ui.Dialog({
        title: 'Bank Account details',
        fields: [
          {
            label: 'Bank Account',
            fieldname: 'bank',
            fieldtype: 'Link',
            options: 'Bank Account'
          }
        ],
        size: 'small',
        primary_action_label: 'Submit',
        primary_action(values) {
          var child_row = child_rows.mapping_bank
          for (var i = 0; i < child_row.length; i++) {
            frappe.model.set_value("Bank Account Mapping", child_row[i], "bank_account", values.bank)
            frm.refresh_field("mapping_bank")
          }
          d.hide();
        }
      });
      d.show();
    }
  }
}

frappe.ui.form.on('File upload', {
    download_template: function(frm) {
      let template_name = null;
      let template_doctype = null;

      switch (frm.doc.document_type) {
        case 'Debtors Report':
          template_name = 'Bill';
          break;
        case 'Claim Book':
          template_name = 'ClaimBook';
          break;
        case 'Settlement Advice':
          template_doctype = 'Customer';
          template_name = frm.doc.payer_type;
          break;
        case 'Bank Statement':
          template_name = 'Bank Transaction'
          break;
        case 'Bill Adjustment':
          template_name = 'Bill Adjustment';
          break;
        case 'Write Back':
          template_name = 'Write Back';
          break;
        case 'Write Off':
          template_name = 'Write Off';
          break;
        case 'Bank Statement Bulk':
          template_name = 'Bank Transaction';
          break;
        default:
          template_name = null;
          template_doctype = null
          break;
      }
      if(template_name === null){
        frappe.msgprint('Template Not Available')
      }
      else{
      frappe.call({
          method: 'agarwals.utils.file_util.is_template_exist',
          args: {
            attached_to_name: template_name,
            attached_to_doctype: template_doctype
          },
          callback: function (r) {
            if(r.message === 'Not Found' || r.message === 'System Error'){
              frappe.msgprint('Message: Template Not Available')
            }
            else{
              window.open(r.message)
            }
      }})
    }}}
)