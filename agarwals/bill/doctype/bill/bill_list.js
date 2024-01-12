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
			frappe.call({
			    method: "agarwals.utils.importation_and_doc_creation.create_physical_claim_submission",
			    args:{
			        bill_no_array:bill_no_array
			    },
			    callback: function(r){
			        var return_msg = r.message
			        console.log(r.message)
			        if(return_msg[0] == "Success"){
			            window.location.href = '/app/physical-claim-submission/' + return_msg[1]
			        }
			    }
			})
		});
    }
};
