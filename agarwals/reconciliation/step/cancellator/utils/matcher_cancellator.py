import frappe
from  agarwals.utils.error_handler import log_error

class MatcherCancellator:
    def delete_matcher(self,sales_invoice_record):
        try:
            matcher_records =  frappe.get_list('Matcher',filters = {'sales_invoice':sales_invoice_record.name},pluck='name')
            for matcher_record in matcher_records:
                  matcher_record = frappe.get_doc('Matcher',matcher_record)
                  if matcher_record:
                    if matcher_record.settlement_advice:
                      sa_record = frappe.get_doc('Settlement Advice',matcher_record.settlement_advice)
                      sa_record.update({
					   "status":"Warning",
                       "remark":"Cancelled Bill" 
				       })
                      sa_record.save()
                    if matcher_record.claimbook:
                      claimbook = frappe.get_doc('ClaimBook',matcher_record.claimbook)
                      claimbook.update({
						  "matched_status": None
					  })
                      claimbook.save()
                    frappe.db.sql(f"Delete from `tabMatcher` where name = '{matcher_record.name}'")
                   
        except Exception as e:
            log_error(e,'Sales Invoice',sales_invoice_record.name)

        finally:
            frappe.db.commit()