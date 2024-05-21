// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

frappe.ui.form.on('Settlement Advice Downloader UI', {
		refresh:function(frm) {
        if (frm.doc.captcha_img) {
			var captchaField = frm.fields_dict['captcha_html'].$wrapper;
			captchaField.empty();
			var imgElement = $('<img>').attr('src', frm.doc.captcha_img);
			captchaField.append(imgElement);
        }
		else{
			var captchaField = frm.fields_dict['captcha_html'].$wrapper;
			captchaField.empty();
		}

    },
	next:function(frm) {
		if (frm.doc.status == 'InProgress') {
			frm.save()
			frm.refresh()
			frappe.call({
				method: 'agarwals.reconciliation.step.advice_downloader.download_captcha_settlement_advice',
				args: {
					'captcha_tpa_doc': frm.doc.name
				}
			})

		}
	},
	after_save:function(frm){
			if(frm.doc.retry_invalid_captcha == 1){
			frappe.call({
				method:"agarwals.agarwals.doctype.settlement_advice_downloader_ui.settlement_advice_downloader_ui.update_logins",
				args: {
					'doc_name': frm.doc.name
				}
			})
			}
	},
	onload_post_render: function(frm) {
		frm.fields_dict.next.$input.css({
			'font-size': '16px',
			"text-align": "center",
			"background-color": "#42a5fc",
			"color": "white",
			"height": "40px",
			"width": "150px",
			"margin": "0 auto",
			"display": "block"
		});
	}


});
