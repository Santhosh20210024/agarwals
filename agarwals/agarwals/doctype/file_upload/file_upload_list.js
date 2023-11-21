frappe.listview_settings['File Upload'] = {
    onload(listview) {
        let d = new frappe.ui.Dialog({
            title: 'Confirm the Bank Entry',
            fields: [
             {label: "Enter 'yes' to confirm:",
            fieldname: 'first_name',
            fieldtype: 'Data'}
            ],
            size: 'small',
            primary_action_label: 'Submit',
            primary_action(values){
                console.log(values)
                if(values = "yes"){
                frappe.call({
                    method:"agarwals.agarwals.doctype.file_upload.file_upload.bank_entry_operation",
                    async:false,
                    callback:function(r){
                        if(r.message != "Success"){
                            frappe.throw("Error While Tranforming the File")
                        }
                    }
                })
                d.hide();
            }}
        })

        var load = function(){
            frappe.call({
                method:"agarwals.agarwals.doctype.file_upload.file_upload.loading",
                callback:function(r){
                    if(r.message != "Success"){
                        frappe.throw("Error While Loading the File")
                    }
                }
            })
        }


        listview.page.add_inner_button('Transform', () => d.show())
        listview.page.add_inner_button('Load', () => load())

}
}
