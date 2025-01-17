// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

frappe.ui.form.on('SA Downloader Configuration', {
    before_save: function (frm) {
        if (frm.doc.days <= 0) {
            frappe.msgprint({
                title: __('Warning'),
                indicator: 'orange',
                message: __('The days field must be greater than zero. Setting to default value of 29.')
            });
            frm.set_value('days', 29);
        }

        if (frm.doc.to_date < frm.doc.from_date) {
            frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __('To Date cannot be less than From Date')
            });
            frappe.validated = false; 

        }
    }
});
