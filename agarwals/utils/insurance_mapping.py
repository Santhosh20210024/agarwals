import frappe
import re
import string

INSURANCE_TAG = 'Insurance'

def normalize_text(text):
    # remove new line & carriage return from text & lowercase
    return text.translate({ ord(_text): None for _text in string.whitespace }).lower()

def get_pattern_list(pattern_type):
    return frappe.get_list('Insurance Pattern', filters = {'pattern_type' : pattern_type}, pluck = "pattern")

def compile_patterns(patterns):
    return '(?:%s)' % '|'.join(normalize_text(pattern) for pattern in patterns)
 
def format_utr(utr):
    if type(utr) is dict:
        utr_key = list(utr.keys())[0]
        utr_value = list(utr.values())[0]
        utr[utr_key] = utr_value.strip().lstrip('0').lstrip("'")
        return utr
    
    return utr.strip().lstrip('0').lstrip("'")

def advice_rfn_match(_doctype=None):
    try:
        staging_utr_list = frappe.db.sql("""SELECT name, tag, reference_number from `tabBank Transaction Staging` where tag is NULL and staging_status != 'Processed' and reference_number != 0""",as_dict=1)
        advices_utr_list = frappe.db.sql("""SELECT utr_number from `tabSettlement Advice` where utr_number IS NOT NULL and utr_number != 0""", as_dict=1)
        staging_name_rfn = list(map( format_utr, [{entry['name']: entry['reference_number']} for entry in staging_utr_list if 'reference_number' in entry and 'name' in entry]))
        advices_rfn = list(map(format_utr, [ entry['utr_number'] for entry in advices_utr_list if 'utr_number' in entry]))

        # Intersection
        staging_rfn = []
        for staging_record in staging_name_rfn:
            staging_rfn.append(list(staging_record.values())[0])

        matched_rfn = list(set(staging_rfn) & set(advices_rfn))

        matched_name = []
        for _name_rfn_item in staging_name_rfn:
            if list(_name_rfn_item.values())[0] in matched_rfn:
                matched_name.append(list(_name_rfn_item.keys())[0])

        for doc_name in matched_name:
                frappe.db.sql("""
                            UPDATE `tabBank Transaction Staging` SET tag = %(tag)s, based_on = 'Settlement Advice' where name = %(name)s
                            """, values = { 'tag' : INSURANCE_TAG, 'name' : doc_name})
                frappe.db.commit()
    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', 'Bank Transaction Staging')
        error_log.set('error_message', str(e)) 
        error_log.save()

def rm_transactions():
    trns_list = frappe.db.sql("SELECT * FROM `tabBank Transaction` tbt INNER JOIN `tabBank Transaction Staging` tbts ON tbts.reference_number = tbt.reference_number where tag IS NULL and tbts.staging_status = 'Processed'", as_dict = 1)
    
    for trns_item in trns_list:
        if frappe.get_value('Bank Transaction', trns_item.reference_number, "status") != 'Reconciled':
            frappe.db.sql("DELETE FROM `tabBank Transaction` where name = %(reference_number)s", values = {'reference_number' : trns_item.reference_number})
            frappe.set_value('Bank Transaction Staging', trns_item.name, "staging_status", "Open" )
            frappe.db.commit()

        else:
            bts = frappe.get_doc("Bank Transaction Staging", trns_item.name )
            if bts.staging_status != 'Error':
                bts.staging_status = 'Error'
                bts.remarks = ' Insurance Tag is removed by user but the transaction is already reconciled'
                bts.save()
                frappe.db.commit()

@frappe.whitelist()
def tag_insurance_pattern(doctype=None): 
    # Verify the field is exsit
    if not frappe.get_meta(doctype).has_field('description'): 
        frappe.throw(f'Description field does not exist in {doctype} doctype')

    inclusion_patterns = get_pattern_list('Inclusion')
    exclusion_patterns = get_pattern_list('Exclusion') 

    compressed_inclusion_patterns = compile_patterns(inclusion_patterns) 
    compressed_exclusion_patterns = compile_patterns(exclusion_patterns) 

    #Inclusion Pattern
    try:
        if compressed_inclusion_patterns:   

            # Truncate the 'TAG' column intially 
            frappe.db.sql("""UPDATE `tabBank Transaction Staging` SET tag = NULL, based_on = NULL where tag = %(tag)s""", values = { 'tag' : INSURANCE_TAG})
            frappe.db.commit()

            frappe.db.sql("""
                        UPDATE `tabBank Transaction Staging` SET tag = %(tag)s where search REGEXP %(compressed_inclusion_patterns)s
                        """, values = { 'tag' : INSURANCE_TAG, 'compressed_inclusion_patterns' : compressed_inclusion_patterns})
            frappe.db.commit()

        else:
            frappe.throw('Inclusion Patterns is not found')

    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', 'Bank Transaction Staging')
        error_log.set('error_message', str(e)) 
        error_log.save()
        
    #Exclusion Pattern
    try:
        if compressed_exclusion_patterns:
            frappe.db.sql("""
                        UPDATE `tabBank Transaction Staging` SET tag = NULL where tag = %(_tag)s AND search REGEXP %(compressed_exclusion_patterns)s
                        """, values = { '_tag' : INSURANCE_TAG, 'compressed_exclusion_patterns' : compressed_exclusion_patterns})
            frappe.db.commit()
        else:
            frappe.throw('Exclusion Patterns is not found')

        frappe.db.sql("""
                      UPDATE `tabBank Transaction Staging` SET based_on = 'Insurance Pattern' where tag = %(_tag)s
                      """, values = {'_tag' : INSURANCE_TAG})
        frappe.db.commit()
        
        rm_transactions()
        advice_rfn_match(_doctype=doctype)
        # frappe.db.sql("""
        #               UPDATE `tabBank Transaction Stagging` SET based_on = `Insurance Pattern` where tag = %(_tag)s
        #               """, values = {'_tag' : INSURANCE_TAG})
        # frappe.db.commit()

    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', 'Bank Transaction Staging')
        error_log.set('error_message', str(e))
        error_log.save()

    return "Done"