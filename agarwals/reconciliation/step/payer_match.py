import frappe
from agarwals.reconciliation.step.insurance_tagger import compile_patterns, normalize_text
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error


# Custom_payer_priority
# Include the missing search field value in bank transaction staging
def update_search_field():
    search_list = frappe.get_list('Bank Transaction Staging', filters = {'search': ["is", "not set"]}, fields = ['name', 'description'])
    for search_item in search_list:
        if search_item.description:
            if search_item.description.strip():
                staging_doc = frappe.get_doc('Bank Transaction Staging', search_item.name)
                staging_doc.search = normalize_text(staging_doc.description)
                staging_doc.save()
                frappe.db.commit()

def update_payer(customer_list):
     for customer_item in customer_list:
        if customer_item.custom_payer_match:
            compressed_payer_match = compile_patterns(str(customer_item.custom_payer_match).split(','))
            frappe.db.sql("""
                          UPDATE `tabBank Transaction Staging` tbt SET tbt.payer_type = 'Customer', tbt.payer_name = %(payer)s,
                          tbt.payer_group = %(payer_group)s where search REGEXP %(compressed_payer_match)s 
                          AND ( tbt.payer_name is NULL or tbt.payer_name = 'TPA Receipts' )
                          """, values = { 'payer' : customer_item.name , 'payer_group' : customer_item.customer_group 
                          ,'compressed_payer_match' :  compressed_payer_match})
            frappe.db.commit()
    
def update_tpa_receipts():
     frappe.db.sql("""
                    UPDATE `tabBank Transaction Staging` tbt SET tbt.payer_type = 'Customer', 
                    tbt.payer_name = %(payer)s, tbt.payer_group = %(payer_group)s where tbt.payer_name is NULL
                    """, values = { 'payer' : 'TPA Receipt', 'payer_group' : 'TPA/INSURANCE'})
     frappe.db.commit()

def map_payer():
    # Update the search field if not exist
    update_search_field()    

    # Based On Priority
    customer_list = frappe.get_list(
    'Customer', fields=['name', 'custom_payer_match', 'customer_group'],
    filters={'custom_payer_match': ["is", "set"],'custom_payer_priority': ["is", "set"]},
    order_by='custom_payer_priority asc'
    )
    update_payer(customer_list)

    # Update without Priority
    customer_list = frappe.get_list(
    'Customer', fields=['name', 'custom_payer_match', 'customer_group'],
    filters={'custom_payer_match': ["is", "set"],'custom_payer_priority': ["is", "not set"]},
    )
    update_payer(customer_list)
    update_tpa_receipts()
    

@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "InProgress")
        try:
            map_payer()
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            log_error(e, 'Step')
            chunk.update_status(chunk_doc, "Error")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')
