frappe.listview_settings['Bill'] = {
    onload(listview) {
    //For Viewing UnVerified Bills
        listview.page.add_inner_button('View Unverified Bills', () => {
            window.location.href = '/app/bill?verified=0';
        });

    //For Creating the Physical Claim Submission using Bulk select and Create
        listview.page.add_action_item(__("Physical Claim Submission"), ()=>{
			let check_items = listview.get_checked_items();
			var bill_no_array = []
			for(var i = 0; i<check_items.length; i++){
			    bill_no_array.push(check_items[i]['name'])
			}
		});
    }
};
