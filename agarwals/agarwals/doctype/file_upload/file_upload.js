// Copyright (c) 2023, Agarwals and contributors
// For license information, please see license.txt



// App Created Modiftion done
// Toggle Part Done
// File Storage
// Email Notification



frappe.ui.form.on('File Upload', {
	refresh: function (frm) {

        frm.fields_dict['type'].df.onchange = function () {
            show_hide_fields(frm);
        };
        
        show_hide_fields(frm);
		set_css(frm)
    },
	reload: function (frm) {

        frm.fields_dict['type'].df.onchange = function () {
            show_hide_fields(frm);
        };
        
        show_hide_fields(frm);
		set_css(frm)
    }
});


// Function to show/hide fields based on dropdown value
function show_hide_fields(frm) {
    var selected_value = frm.doc.type;

    // Hide all fields initially
    frm.toggle_display(['bank_account', 'debtor', 'upload'], false);

    if (selected_value === 'Bank Statement') {
        frm.toggle_display(['bank_account', 'upload'], true);
		frm.set_df_property('bank_account', 'reqd', 1);
		frm.set_df_property('debtor', 'reqd', 0);
    } else if (selected_value === 'Debtor Statement') {
        frm.toggle_display(['debtor', 'upload'], true);
		frm.set_df_property('bank_account', 'reqd', 0);
		frm.set_df_property('debtor', 'reqd', 1);
    } else if (selected_value === 'Bill'){
        frm.toggle_display(['upload'], true);
    } else if (selected_value === 'ClaimBook'){
        frm.toggle_display(['upload'], true);
    }
    
}

var set_css = function (frm)
    {
	
	// Dropdown Icon
	document.querySelector('div.select-icon').style.display = "none"

	// Type Styling
    document.querySelectorAll("[data-fieldname='type']")[1].style.height ="40px";
    document.querySelectorAll("[data-fieldname='type']")[1].style.width ="300px";
	document.querySelectorAll("[data-fieldname='type']")[1].style.fontWeight ="bold";
	
	// bank Account
	document.querySelectorAll("[data-fieldname='bank_account']")[1].style.height ="40px";
    document.querySelectorAll("[data-fieldname='bank_account']")[1].style.width ="300px";
	// document.querySelectorAll("[data-fieldname='bank_account']")[1].style.fontWeight ="bold";

	// debtor
	document.querySelectorAll("[data-fieldname='debtor']")[1].style.height ="40px";
    document.querySelectorAll("[data-fieldname='debtor']")[1].style.width ="300px";

    }
