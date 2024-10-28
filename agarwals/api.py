import json
import frappe

@frappe.whitelist()
def get_user_name():
    return json.dumps(frappe.session.username)