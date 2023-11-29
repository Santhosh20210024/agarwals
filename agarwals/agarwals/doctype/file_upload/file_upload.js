frappe.ui.form.on('File Upload', {
	refresh: function (frm) {
		set_css(frm)
    },
	reload: function (frm) {
		set_css(frm)
    }
});


// Need to refactor later
var set_css = function (frm){
    //debtor_report_upload
    document.querySelectorAll("[data-fieldname='debtor_report_upload']")[1].style.backgroundColor ="black";
    document.querySelectorAll("[data-fieldname='debtor_report_upload']")[1].style.color ="white";  

    //claimbook_upload
    document.querySelectorAll("[data-fieldname='claimbook_upload']")[1].style.backgroundColor ="black";
    document.querySelectorAll("[data-fieldname='claimbook_upload']")[1].style.color ="white";  

    //settlement_advice_upload
    document.querySelectorAll("[data-fieldname='settlement_advice_upload']")[1].style.backgroundColor ="black";
    document.querySelectorAll("[data-fieldname='settlement_advice_upload']")[1].style.color ="white";  

    //bank_statement_upload
    document.querySelectorAll("[data-fieldname='bank_statement_upload']")[1].style.backgroundColor ="black";
    document.querySelectorAll("[data-fieldname='bank_statement_upload']")[1].style.color ="white";  

}