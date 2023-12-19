// Copyright (c) 2023, Agarwals and contributors
// For license information, please see license.txt

frappe.ui.form.on('File uploader', {
	onload: function(frm) {
		

	 }
});
frappe.ui.form.on('File uploader', {
	refresh: function (frm) {
		set_css(frm)
    },
	reload: function (frm) {
		set_css(frm)
    }
});

var set_css = function (frm){
    //debtor_report_upload
    document.querySelectorAll("[data-fieldname='upload']")[1].style.backgroundColor ="#2490EF";
    document.querySelectorAll("[data-fieldname='upload']")[1].style.color ="white"; 
}