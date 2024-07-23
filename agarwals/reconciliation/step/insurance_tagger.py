import frappe
import string
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
INSURANCE_TAG = 'Credit Payment'

def normalize_text(text):
    # remove new line & carriage return from text & lowercase
    return text.translate({ ord(_text): None for _text in string.whitespace }).lower()

def get_pattern_list(pattern_type):
    return frappe.get_list('Insurance Pattern', filters = {'pattern_type' : pattern_type}, pluck = "pattern")

def compile_patterns(patterns):
    return '(?:%s)' % '|'.join(normalize_text(pattern) for pattern in patterns)

def advices_rfn_match():
    try: 
        frappe.db.sql("""
        update `tabBank Transaction Staging` tbts, `tabSettlement Advice` tsa set tbts.tag = %(tag)s, tbts.based_on = 'Settlement Advice'
        where (tbts.reference_number = tsa.cg_formatted_utr_number) and tbts.tag is null and tbts.reference_number != '0';
        """, values = {'tag' : INSURANCE_TAG})
        frappe.db.commit()
        frappe.db.sql("""
        update `tabBank Transaction Staging` tbts, `tabSettlement Advice` tsa set tbts.tag = %(tag)s, tbts.based_on = 'Settlement Advice'
        where (tbts.reference_number = tsa.final_utr_number) and tbts.tag is null and tbts.reference_number != '0';
        """, values = {'tag' : INSURANCE_TAG})
        frappe.db.commit()
        frappe.db.sql("""
        update `tabBank Transaction Staging` tbts, `tabSettlement Advice` tsa set tbts.tag = %(tag)s, tbts.based_on = 'Settlement Advice'
        where (tbts.reference_number = tsa.utr_number) and tbts.tag is null and tbts.reference_number != '0';
        """, values = {'tag' : INSURANCE_TAG})
        frappe.db.commit()
        print("Advice Process Completed")
    except Exception as e:
        log_error(error=str(e),doc="Bank Transaction Staging")
        # error_log = frappe.new_doc('Error Record Log')
        # error_log.set('doctype_name', 'Bank Transaction Staging')
        # error_log.set('error_message', str(e))
        # error_log.save()

def claimbook_match():
        frappe.db.sql(""" 
        UPDATE `tabBank Transaction Staging` tbts ,`tabClaimBook` cb set tbts.tag = %(tag)s, tbts.based_on = 'ClaimBook'
        where (tbts.reference_number = cb.utr_number) and tbts.tag is null and tbts.reference_number != '0' and cb.utr_number != '0';
        """, values = {'tag': INSURANCE_TAG })
        frappe.db.commit()
        frappe.db.sql(""" 
           UPDATE `tabBank Transaction Staging` tbts ,`tabClaimBook` cb set tbts.tag = %(tag)s, tbts.based_on = 'ClaimBook'
        where (tbts.reference_number = cb.final_utr_number) and tbts.tag is null and tbts.reference_number != '0' and cb.utr_number != '0';
        """, values = {'tag': INSURANCE_TAG })
        frappe.db.sql(""" 
           UPDATE `tabBank Transaction Staging` tbts ,`tabClaimBook` cb set tbts.tag = %(tag)s, tbts.based_on = 'ClaimBook'
        where (tbts.reference_number = cb.cg_formatted_utr_number) and tbts.tag is null and tbts.reference_number != '0' and cb.utr_number != '0';
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
def process(args):
    try:
        args=cast_to_dic(args)
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "InProgress")
        try:
            if not frappe.get_meta(args["doctype"]).has_field('description'):
                frappe.throw(f'Description field does not exist in {args["doctype"]} doctype')
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
                log_error(error=str(e), doc="Bank Transaction Staging")
            #Exclusion Pattern
            try:
                # search is mandatory to follow
                if compressed_exclusion_patterns:
                    frappe.db.sql("""
                                UPDATE `tabBank Transaction Staging` SET tag = NULL, based_on = NULL where tag = %(_tag)s AND search REGEXP %(compressed_exclusion_patterns)s and based_on is NULL and is_fixed != 1
                                """, values = { '_tag' : INSURANCE_TAG, 'compressed_exclusion_patterns' : compressed_exclusion_patterns})
                    frappe.db.commit()
                else:
                    frappe.throw('Exclusion Patterns is not found')
                frappe.db.sql("""
                            UPDATE `tabBank Transaction Staging` SET based_on = 'Insurance Pattern' where tag = %(_tag)s and based_on is NULL and is_fixed != 1
                            """, values = {'_tag' : INSURANCE_TAG})
                frappe.db.commit()
                print("Exclusion Process Completed")
                advices_rfn_match()
                claimbook_match()
                rm_transactions()
            except Exception as e:
                log_error(error=str(e), doc="Bank Transaction Staging")
                # error_log = frappe.new_doc('Error Record Log')
                # error_log.set('doctype_name', 'Bank Transaction Staging')
                # error_log.set('error_message', str(e))
                # error_log.save()
                # frappe.db.commit()
            chunk.update_status(chunk_doc, "Processed")
            return "Done"
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')