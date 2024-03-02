import frappe
import string

INSURANCE_TAG = 'Credit Payment'

def normalize_text(text):
    # remove new line & carriage return from text & lowercase
    return text.translate({ ord(_text): None for _text in string.whitespace }).lower()

def get_pattern_list(pattern_type):
    return frappe.get_list('Insurance Pattern', filters = {'pattern_type' : pattern_type}, pluck = "pattern")

def compile_patterns(patterns):
    return '(?:%s)' % '|'.join(normalize_text(pattern) for pattern in patterns)

def advices_rfn_match():
    try:    # needd to chenage
        
        print("advice 1")
        frappe.db.sql("""
        update `tabBank Transaction Staging` tbts, `tabSettlement Advice` tsa set tbts.tag = %(tag)s, tbts.based_on = 'Settlement Advice'
        where (tbts.reference_number = tsa.cg_formatted_utr_number) and tbts.tag is null and tbts.reference_number != '0';
        """, values = {'tag' : INSURANCE_TAG})

        frappe.db.commit()

        print("advice 2")
        frappe.db.sql("""
        update `tabBank Transaction Staging` tbts, `tabSettlement Advice` tsa set tbts.tag = %(tag)s, tbts.based_on = 'Settlement Advice'
        where (tbts.reference_number = tsa.final_utr_number) and tbts.tag is null and tbts.reference_number != '0';
        """, values = {'tag' : INSURANCE_TAG})

        frappe.db.commit()
    
        print("advice 3")
        frappe.db.sql("""
        update `tabBank Transaction Staging` tbts, `tabSettlement Advice` tsa set tbts.tag = %(tag)s, tbts.based_on = 'Settlement Advice'
        where (tbts.reference_number = tsa.utr_number) and tbts.tag is null and tbts.reference_number != '0';
        """, values = {'tag' : INSURANCE_TAG})

        frappe.db.commit()

        # frappe.db.sql(""" 
        #     UPDATE `tabBank Transaction Staging` tbts JOIN `tabSettlement Advice` tsa ON tbts.reference_number = tsa.final_utr_number
        #     SET tbts.tag = %(tag)s 
        #     WHERE tbts.tag IS NULL 
        #     AND tbts.staging_status != 'Processed'
        #     AND tsa.final_utr_number IS NOT NULL
        # """, values = {'tag': INSURANCE_TAG })


        # frappe.db.sql(""" 
        #     UPDATE `tabBank Transaction Staging` tbts JOIN `tabSettlement Advice` tsa ON TRIM(LEADING '0' FROM source_reference_number) = tsa.cg_utr_number
        #     SET tag = %(tag)s, based_on = 'Settlement Advice' 
        #     WHERE tbts.tag IS NULL 
        #     AND tbts.staging_status != 'Processed'
        #     AND tsa.cg_utr_number IS NOT NULL
        # """, values = {'tag': INSURANCE_TAG })

        print("Advice Process Completed")

    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', 'Bank Transaction Staging')
        error_log.set('error_message', str(e)) 
        error_log.save()

def claimbook_match():
        
        print("claim 1")
        frappe.db.sql(""" 
        UPDATE `tabBank Transaction Staging` tbts ,`tabClaimBook` cb
        where (tbts.reference_number = cb.utr_number) and tbts.tag is null and tbts.reference_number != '0' and cb.utr_number != '0';
        """, values = {'tag': INSURANCE_TAG })
        frappe.db.commit()

        print("claim 2")
        frappe.db.sql(""" 
           UPDATE `tabBank Transaction Staging` tbts ,`tabClaimBook` cb
        where (tbts.reference_number = cb.final_utr_number) and tbts.tag is null and tbts.reference_number != '0' and cb.utr_number != '0';
        """, values = {'tag': INSURANCE_TAG })
        frappe.db.commit()
        print("ClaimBook Process Completed")

def delete_corrs_doc(doctype_name, doc_name):
    frappe.get_doc(doctype_name, doc_name).cancel()
    frappe.delete_doc(doctype_name, doc_name)
    trans = frappe.new_doc('Transaction Delete Log')
    trans.doctype_name = 'Bank Transaction'
    trans.message = f'{doc_name} is deleted'
    trans.save()
    frappe.db.commit()

def rm_transactions():
    trns_list = frappe.db.sql("SELECT * FROM `tabBank Transaction` tbt INNER JOIN `tabBank Transaction Staging` tbts ON tbts.reference_number = tbt.reference_number where tag IS NULL and tbts.staging_status = 'Processed'", as_dict = 1)
    
    for trns_item in trns_list:
        if int(frappe.get_value('Bank Transaction', trns_item.reference_number, "allocated_amount")) == 0: #
            # frappe.db.sql("DELETE FROM `tabBank Transaction` where name = %(reference_number)s", values = {'reference_number' : trns_item.reference_number})
            delete_corrs_doc('Bank Transaction', trns_item.reference_number)
            frappe.set_value('Bank Transaction Staging', trns_item.name, "staging_status", "Skipped" )
            frappe.db.commit()

        else:
            bts = frappe.get_doc("Bank Transaction Staging", trns_item.name )
            if 'E106:' not in bts.error:
                bts.staging_status = 'Error'
                bts.error = 'E106: Insurance Tag is removed by user but the transaction is already reconciled'
                bts.remarks = ''
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
            frappe.db.sql("""UPDATE `tabBank Transaction Staging` SET tag = NULL, based_on = NULL where tag = %(tag)s and based_on = %(type)s and is_fixed != 1""", values = { 'tag' : INSURANCE_TAG, 'type': 'Insurance Pattern'})
            frappe.db.commit()

            frappe.db.sql("""
                        UPDATE `tabBank Transaction Staging` SET tag = %(tag)s where search REGEXP %(compressed_inclusion_patterns)s and based_on is NULL and is_fixed != 1
                        """, values = { 'tag' : INSURANCE_TAG, 'compressed_inclusion_patterns' : compressed_inclusion_patterns})
            frappe.db.commit()

        else:
            frappe.throw('Inclusion Patterns is not found')

        print("Inclusion Process Completed")

    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', 'Bank Transaction Staging')
        error_log.set('error_message', str(e)) 
        error_log.save()
        frappe.db.commit()
        
    #Exclusion Pattern
    try:
        # search is mandatory to follow
        if compressed_exclusion_patterns:
            frappe.db.sql("""
                         UPDATE `tabBank Transaction Staging` SET tag = NULL, based_on = NULL where tag = %(_tag)s AND search REGEXP %(compressed_exclusion_patterns)s and based_on is NULL
                         """, values = { '_tag' : INSURANCE_TAG, 'compressed_exclusion_patterns' : compressed_exclusion_patterns})
            frappe.db.commit()
        else:
            frappe.throw('Exclusion Patterns is not found')

        frappe.db.sql("""
                      UPDATE `tabBank Transaction Staging` SET based_on = 'Insurance Pattern' where tag = %(_tag)s and based_on is NULL
                      """, values = {'_tag' : INSURANCE_TAG})
        frappe.db.commit()
        
        print("Exclusion Process Completed")
        advices_rfn_match()
        claimbook_match()
        rm_transactions() 

    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', 'Bank Transaction Staging')
        error_log.set('error_message', str(e))
        error_log.save()
        frappe.db.commit()

    return "Done"
