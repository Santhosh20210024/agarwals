frappe.ui.form.on('Physical Claim Submission', {
    refresh: function(frm) {
        frm.fields_dict['bill_list'].get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    verified: 1
                }
            };
        };
    }
});
