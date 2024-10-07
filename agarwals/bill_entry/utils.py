import frappe

def delete_bill_event(bill, event, date, mode_of_submission):
    bill_tracker_list = frappe.get_all("Bill Tracker", filters={'event': event, 'date': date, 'parent': bill},
                                       pluck='name')
    for bill_tracker in bill_tracker_list:
        if mode_of_submission:
            frappe.db.set_value("Sales Invoice", bill, "custom_mode_of_submission", "")
        bill_tracker = frappe.get_doc('Bill Tracker', bill_tracker)
        bill_tracker.cancel()
        bill_tracker.delete(ignore_permissions=True)
        frappe.db.commit()


def update_bill_event(bill, event, date, mode_of_submission, remark, ma_claim_id = None):
    bill_entry_log = frappe.get_doc(
        {'doctype': "Bill Entry Log", "bill": bill, "event": event, "ma_claim_no": ma_claim_id,
         "date": date, "mode_of_submission": mode_of_submission, "remark": remark})
    bill_entry_log.insert()
    frappe.db.commit()