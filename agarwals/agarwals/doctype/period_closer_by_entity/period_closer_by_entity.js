// Copyright (c) 2024, Agarwals and contributors
// For license information, please see license.txt

frappe.ui.form.on('Period Closer by Entity', {
	entity: function(frm) {
        frm.save()
	},
	onload:function(frm){
		if (frm.doc.posting_date){
			frm.set_df_property("posting_date","read_only", 1);
			frm.set_df_property("entity","read_only", 1);
		}
		else {
			frm.set_df_property("posting_date", "hidden", true);
		}
	},
	before_save:function (frm){
		if (frm.doc.entity){
			frm.set_df_property("posting_date", "hidden", false);
		}
	},
	after_save: function (frm){
		if (frm.doc.posting_date){
			frm.set_df_property("posting_date","read_only", 1);
			frm.set_df_property("entity","read_only", 1);
		}
	}
});
