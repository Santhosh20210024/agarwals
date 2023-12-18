frappe.ui.form.on('File Upload', {
	refresh: function (frm) {
		set_css(frm)
    },
	reload: function (frm) {
		set_css(frm)
    }
});

frappe.ui.form.on("File Upload", "refresh", function(frm) {
  frm.set_df_property( "payer_type", "read_only", frm.is_new() ? 0 : 1);
  frm.set_df_property( "bank_account", "read_only", frm.is_new() ? 0 : 1);
})

var set_css = function (frm){
    //debtor_report_upload
    document.querySelectorAll("[data-fieldname='debtor_report_upload']")[1].style.backgroundColor ="#2490EF";
    document.querySelectorAll("[data-fieldname='debtor_report_upload']")[1].style.color ="white";  

    //claimbook_upload
    document.querySelectorAll("[data-fieldname='claimbook_upload']")[1].style.backgroundColor ="#2490EF";
    document.querySelectorAll("[data-fieldname='claimbook_upload']")[1].style.color ="white";  

    //settlement_advice_upload
    document.querySelectorAll("[data-fieldname='settlement_advice_upload']")[1].style.backgroundColor ="#2490EF";
    document.querySelectorAll("[data-fieldname='settlement_advice_upload']")[1].style.color ="white";  

    //bank_statement_upload
    document.querySelectorAll("[data-fieldname='bank_statement_upload']")[1].style.backgroundColor ="#2490EF";
    document.querySelectorAll("[data-fieldname='bank_statement_upload']")[1].style.color ="white";

    //
    document.querySelectorAll("[data-fieldname='physical_claim_upload']")[1].style.backgroundColor ="#2490EF";
    document.querySelectorAll("[data-fieldname='physical_claim_upload']")[1].style.color ="white";
}