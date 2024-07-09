import frappe

class MatcherReferenceCancellator:
    def delete_matcher_reference(self, bill):
        frappe.db.sql(f"DELETE FROM `tabMatcher Reference` WHERE parent= '{bill}' ")
