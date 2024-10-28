import json
import frappe

@frappe.whitelist()
def get_user_name():
    user_email = frappe.session.user
    return frappe.get_doc('User',user_email).full_name

@frappe.whitelist()
def create_bill_entry(bill, ma_claim_id, events, date, remarks,mode):
  try:
    bill_entry = frappe.get_doc({
        'doctype': 'Bill Entry Log',  
        'bill': bill,
        'ma_claim_no': ma_claim_id,
        'event': events,
        'date': date,
        'remark': remarks,
        'mode_of_submission':mode,
    })
    bill_entry.insert()
    return {'message': 'Bill entry created successfully', 'bill_id': bill_entry.name}
  except Exception as e:
      print("Error")