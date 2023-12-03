// Copyright (c) 2023, Agarwals and contributors
// For license information, please see license.txt

 frappe.ui.form.on("Physical Claim Submission", {
 	refresh(frm) {
 		var currentDateTimeUTC = new Date();
		var utcTime = currentDateTimeUTC.getTime();
		var istOffset = 5.5 * 60 * 60 * 1000;
		var istTime = utcTime + istOffset;
		var currentDateTimeIST = new Date(istTime);
		var isoStringIST = currentDateTimeIST.toISOString().replace('T', ' ').slice(0, 19)

		frm.set_value('submission_date',isoStringIST)
 	},
 });
