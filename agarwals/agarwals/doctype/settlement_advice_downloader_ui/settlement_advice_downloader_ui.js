// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

var interval_ID = ""
var i = 0
frappe.ui.form.on('Settlement Advice Downloader UI', {

		refresh:function(frm) {
			i = i+1
			console.log(i)
        if (frm.doc.captcha_img && frm.doc.captcha_img != '') {
			var captchaField = frm.fields_dict['captcha_html'].$wrapper;
			captchaField.empty();
			var imgElement = $('<img>').attr('src', frm.doc.captcha_img);
			captchaField.append(imgElement);
			if (interval_ID != "") {
				clearInterval(interval_ID)
				interval_ID = ""
				console.log("Intrval stopped")
			}

        }
		else{
			var captchaField = frm.fields_dict['captcha_html'].$wrapper;
			captchaField.empty();
		}

    },
	next:function(frm) {
		if (frm.doc.status == 'InProgress') {
			frm.toggle_display('next',0)
			if (frm.doc.disable_auto_refresh == 0){
             interval_ID = setInterval(function() {
                cur_frm.reload_doc()
				 console.log("Time Interval Triggered")
            }, 5000);
			}
			frappe.call({
				method: 'agarwals.reconciliation.step.advice_downloader.download_captcha_settlement_advice',
				args: {
					'captcha_tpa_doc': frm.doc.name
				},callback:function(r){
					frm.toggle_display('next',1)
					cur_frm.reload_doc()

				}
			})

		}
	},
	after_save:function(frm){
			frm.refresh()
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
	},
	disable_auto_refresh:function (frm){
			if(frm.doc.disable_auto_refresh == 1){
				if(interval_ID != ""){
					console.log("stoped Interval")
					clearInterval(intervalID)
				}
				else{
					frappe.msgprint(" Auto Refresh Not Activated ")
				}
			}
	}





});




