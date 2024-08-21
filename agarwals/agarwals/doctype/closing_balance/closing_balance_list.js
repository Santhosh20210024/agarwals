frappe.listview_settings['Closing Balance'] = {
    refresh: function(listview) {
         listview.page.add_inner_button("Validate Closing Balance", function() {
             frappe.confirm(
                 'Are you sure you want to perform this action ?',
                 function (frm) {
                   frappe.call({
                   method: 'agarwals.reconciliation.step.closing_balance_check.check',
                   freeze: true,
                   freeze_message: "Validating...",
                   callback: function (r) {
                   if (r.message) { frappe.msgprint(r.message)}
                 }
                });
               });
         });;
 
         listview.page.add_inner_button("Load Closing Balance", function() {
             frappe.confirm(
                 'Are you sure you want to perform this action ?',
                 function (frm) {
                   frappe.call({
                   method: 'agarwals.reconciliation.step.closing_balance_check.load',
                   freeze: true,
                   freeze_message: "Loading...",
                   callback: function (r) {
                   if (r.message) { frappe.msgprint(r.message)}
                 }
                })
               });
         });;
     },
 };