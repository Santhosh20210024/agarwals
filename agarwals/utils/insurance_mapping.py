import frappe
import re
import string

INSURANCE_TAG = 'Insurance'

# remove new line & carriage return from text
# lowercase
def compress_text(text):
    return text.translate({ord(_text): None for _text in string.whitespace}).lower()

def get_doc_list(doctype, _filters=None):
    if _filters:
        return frappe.get_list(doctype, filters = _filters ,fields=['name', '_user_tags', 'description'])
    return frappe.get_list(doctype, fields = ['name', '_user_tags', 'description'])

def get_pattern_list(pattern_type):
    return frappe.get_list('Insurance Pattern', filters = {'pattern_type' : pattern_type}, pluck = "pattern")

def compile_patterns(patterns):
    return '(?:%s)' % '|'.join(compress_text(pattern) for pattern in patterns)

def advice_utr_process(_doctype=None):
    _doc_list = frappe.get_list(_doctype, filters = {'_user_tags': ['=', None]} ,fields = ['name', '_user_tags', 'reference_number'])
    advice_utr_list = frappe.get_list('Settlement Advice', filters = {'utr_number' : ['!=', None]}, pluck = 'utr_number')

    for doc_item in _doc_list:
        if doc_item._user_tags != None:
            if INSURANCE_TAG in doc_item._user_tags:
                continue

        if doc_item.reference_number in advice_utr_list:
            frappe.db.sql("""UPDATE `tabBank Transaction Stagging`
                SET _user_tags = CONCAT(',',%(tag)s)
                WHERE name = %(name)s;
                """, values = { 'name': doc_item.name, 'tag': INSURANCE_TAG }, as_dict=1)
            
            frappe.db.commit()

@frappe.whitelist()
def tag_insurance_pattern(doctype=None):
    if not frappe.get_meta(doctype).has_field('description'):
        frappe.throw(f'Description field does not exist in {doctype} doctype')

    _doc_list = get_doc_list(doctype)
    inclusion_doc_list = get_doc_list(doctype, _filters = {'_user_tags': ['like', f'%{INSURANCE_TAG}%']})

    inclusion_patterns = get_pattern_list('Inclusion')
    exclusion_patterns = get_pattern_list('Exclusion')

    compressed_inclusion_patterns = compile_patterns(inclusion_patterns)
    compressed_exclusion_patterns = compile_patterns(exclusion_patterns)

    # inclusion pattern applying
    for doc_item in _doc_list:
        if doc_item._user_tags != None:
            if INSURANCE_TAG in doc_item._user_tags:
                continue
            
        compressed_description = compress_text(doc_item.description)
        if re.search(compressed_inclusion_patterns, compressed_description):
            try:
                frappe.db.sql("""UPDATE `tabBank Transaction Stagging`
                SET _user_tags = CONCAT(',',%(tag)s)
                WHERE name = %(name)s;
                """, values = { 'name': doc_item.name, 'tag': INSURANCE_TAG }, as_dict=1)
                frappe.db.commit()

            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bank Transaction Stagging')
                error_log.set('error_message', str(e))
                error_log.save()
                
    # exclusion pattern applying
    for doc_item in inclusion_doc_list:
        compressed_description = compress_text(doc_item.description)
        if re.search(compressed_exclusion_patterns, compressed_description):
            try:
                frappe.db.sql("""
                UPDATE `tabBank Transaction Stagging` SET _user_tags = ',' where name = %(name)s
                """,values = { 'name' : doc_item.name }, as_dict = 1)
                frappe.db.commit()

            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bank Transaction Stagging')
                error_log.set('error_message', str(e))
                error_log.save()

    advice_utr_process(_doctype=doctype)
    return "Success"
