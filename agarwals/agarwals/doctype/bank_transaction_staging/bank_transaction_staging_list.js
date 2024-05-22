frappe.listview_settings['Bank Transaction Staging'] = {
    refresh: function(listview) {
        listview.page.add_inner_button("Process Bank Transaction", function() {
            frappe.confirm(
                'Are you sure you want to perform this action ?',
                function (frm) {
                  frappe.call({
                  method: 'agarwals.reconciliation.step.transcation_creator.process',
                  args: {
                    args: {"tag": "Credit Payment", "step_id":"", "chunk_size":100,"queue":"long"}
                  },
                  freeze: true,
                  freeze_message: "Processing Bank Transaction....",
                  callback: function (r) {
                  if (r.message) { frappe.msgprint(r.message)}
                }
               });
              });
        });;
    },
};