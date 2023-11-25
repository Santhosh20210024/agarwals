frappe.listview_settings['File Upload'] = {
    onload(listview) {

    // Dialog Option need to be later enhancement
    //     let d = new frappe.ui.Dialog({
    //         title: 'Confirm the Bank Entry',
    //         fields: [
    //          {label: "Enter 'yes' to confirm:",
    //         fieldname: 'first_name',
    //         fieldtype: 'Data'}
    //         ],
    //         size: 'small',
    //         primary_action_label: 'Submit',
    //         primary_action(values){
    //             console.log(values)
    //             if(values = "yes"){                
    //             d.hide();
    //         }}
    //     })

    var transform = function(){

            frappe.call({
                method:"agarwals.agarwals.doctype.file_upload.file_upload.bank_entry_operation",
                callback:function(r){
                    if(r.message != "Success"){
                        frappe.throw("Error while tranforming the Files")
                    }
                    else{
                        frappe.msgprint("Files are successfully transformed.")
                    }
                }
            })
        }

        var load = function(){
            frappe.call({
                method:"agarwals.agarwals.doctype.file_upload.file_upload.loading",
                callback:function(r){
                    if(r.message != "Success"){
                        frappe.throw("Error While Loading the File")
                    }
                    else{
                        frappe.msgprint("Files are successfully loaded.")
                    }
                }
            })
        }

        listview.page.add_inner_button('Transform', () => transform())
        listview.page.add_inner_button('Load', () => load())
}}
