frappe.ready(function() {
	frappe.web_form.on('bill', (field, value) => {
 frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Sales Invoice",
                    fields: ["name","posting_date","customer","custom_patient_name","rounded_total","status","custom_claim_id","custom_ma_claim_id"],
                    filters: [
                                ["name", "=", value]
                            ],
                },
                async: false,
                callback: function(r) {
                    frappe.web_form.set_value('bill_date', r.message[0].posting_date);
                    frappe.web_form.set_value('patient_name', r.message[0].custom_patient_name);
                    frappe.web_form.set_value('payer', r.message[0].customer);
                    frappe.web_form.set_value('claim_amount', r.message[0].rounded_total);
                    frappe.web_form.set_value('bill_status', r.message[0].status);
                    frappe.web_form.set_value('claim_no', r.message[0].custom_claim_id);
                    frappe.web_form.set_value('ma_claim_no', r.message[0].custom_ma_claim_id);
                }
        })
});
frappe.web_form.on('event_date', (field, value) => {
    let input_date = new Date(value)
         let current_date = new Date()
         if(current_date > input_date && Math.trunc((current_date - input_date)/(1000*60*60*24)) > 7){
             frappe.msgprint(__('Back Date More than 7 Days is Not Allowed.'));
             frappe.web_form.set_value('event_date', current_date);
         }
         if(input_date > current_date){
             frappe.msgprint(__('Future Date is Not Allowed.'));
             frappe.web_form.set_value('event_date', current_date);
         }
})
})