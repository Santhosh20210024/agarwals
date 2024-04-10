import frappe

from agarwals.utils.insurance_mapping import compile_patterns, normalize_text

def update_untagged_search(): 
    # Mainly created for previous or entries  
    # Need to switch over this while or upload through file i
    untagged_search_list = frappe.get_list('Bank Transaction Staging', filters = {'search': ["is", "not set"]}, fields = ['name', 'description'])
    for untagged_item in untagged_search_list:
        if untagged_item.description:
            if untagged_item.description.strip():
                _doc = frappe.get_doc('Bank Transaction Staging', untagged_item.name)
                _doc.search = normalize_text(_doc.description)
                _doc.save()
                frappe.db.commit()

def update_payer(customer_list):
     for customer_item in customer_list:
        print(customer_item.customer_name)
        if customer_item.custom_payer_match:
            compressed_payer_match = compile_patterns(str(customer_item.custom_payer_match).split(','))

            frappe.db.sql("""
                        UPDATE `tabBank Transaction Staging` tbt SET tbt.payer_type = 'Customer', tbt.payer_name = %(payer)s, tbt.payer_group = %(payer_group)s
                        where search REGEXP %(compressed_payer_match)s AND tbt.payer_name is NULL
                    """, values = { 'payer' : customer_item.customer_name , 'payer_group' : customer_item.customer_group , 'compressed_payer_match' :  compressed_payer_match})
            frappe.db.commit()


# Here, create the custom_payer_match in Customer doctype:
def map_payer():

    update_untagged_search()
    customer_list = frappe.get_list('Customer', fields = ['customer_name', 'custom_payer_match', 'customer_group'], filters = { 'custom_payer_match': ["is", "set"], 'customer_name': ['like', '%insurance%'] })
    update_payer(customer_list)

    customer_list = frappe.get_list('Customer', fields = ['customer_name', 'custom_payer_match', 'customer_group'], filters = { 'custom_payer_match': ["is", "set"], 'customer_name': ['not like', '%insurance%'] })
    update_payer(customer_list)
    
@frappe.whitelist()
def run_mapper(): 
    map_payer()