var set_css = function () {
  document.querySelectorAll("[data-fieldname='upload']")[1].style.backgroundColor = "#2490EF";
  document.querySelectorAll("[data-fieldname='upload']")[1].style.color = "white";
  document.querySelectorAll("[data-action='delete_rows']")[0].style.display = "None";
   
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
function process(frm) {
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
			frm.doc.refresh()
              if (r.message) {
                frappe.msgprint(r.message)
			
              }
            }
          });
})



// upload button

}

frappe.ui.form.on('File upload', {
    extract: function(frm) {
            extract(frm);	
        },process: function(frm) {
            process(frm);
        
    }
}
); 
function extract(frm) {
          let data = null
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
frappe.ui.form.on('File upload',{
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

function update_payer_button(frm){
	var addButton = document.createElement('button');
	addButton.innerText = 'Update';
	addButton.className = 'btn btn-xs btn-secondary grid-add-row';
	
	addButton.addEventListener('click', function() {
		 update_payer(frm)
	});
	if(frm.doc.document_type=="Bank Statement"){
	var gridButtons = frm.fields_dict['mapping_bank'].grid.wrapper.find('.grid-buttons');
	gridButtons.append(addButton);
	}
	if(frm.doc.document_type=="Settlement Advice"){
		var gridButtons = frm.fields_dict['mapping_advice'].grid.wrapper.find('.grid-buttons');
	    gridButtons.append(addButton);
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

var change_zip_status_color=function(){
	const code=document.querySelector("[data-fieldname='zip_status']").querySelector("[class='control-input-wrapper']").querySelector("[class='control-value like-disabled-input']")
	var status=code.innerHTML
	console.log(status)
	 if (status=="Processed" || status=="Processing"){
	  code.style.color="Green"
	 } 
	 else if(status=="Extracted" || status=="Extracting"){
		  code.style.color="Red"
	 } 
}
function update_payer(frm){
	if(frm.doc.document_type=="Settlement Advice"){
	const child_rows=frm.get_selected()
	if(Object.keys(child_rows).length>0){
	let d = new frappe.ui.Dialog({
        title: 'Payer details',
        fields: [
            {
                label: 'Payer',
                fieldname: 'payer',
                fieldtype: 'Link',
				options:'Customer'
            }
        ],
        size: 'small',
        primary_action_label: 'Submit',
        primary_action(values) {
				var child_row = child_rows.mapping_advice
	           for(var i=0;i<child_row.length;i++){
				frappe.model.set_value("Settlement Advice Mapping",child_row[i],"payer_name",values.payer)
				frm.refresh_field("mapping_advice")
			   }
		   d.hide();
        }
    });
    d.show();
}}
if(frm.doc.document_type=="Bank Statement"){
	const child_rows=frm.get_selected()
	console.log(child_rows)
	if(Object.keys(child_rows).length>0){
	let d = new frappe.ui.Dialog({
        title: 'Bank Account details',
        fields: [
            {
                label: 'Bank Account',
                fieldname: 'bank',
                fieldtype: 'Link',
				options:'Bank Account'
            }
        ],
        size: 'small',
        primary_action_label: 'Submit',
        primary_action(values) {
				var child_row = child_rows.mapping_bank
	           for(var i=0;i<child_row.length;i++){
				frappe.model.set_value("Bank Account Mapping",child_row[i],"bank_account",values.bank)
				frm.refresh_field("mapping_bank")
			   }
		   d.hide();
        }
    });
    d.show();
}}
}
