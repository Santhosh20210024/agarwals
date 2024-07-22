import frappe
@frappe.whitelist()
def get_sales_invoice_data(doc_name,jv_ac_name):
    child_table = []
    parent_payment_entry = frappe.db.sql(f"SELECT parent FROM `tabPayment Entry Reference` WHERE reference_name ='{doc_name}' ",pluck ='parent')
    jv= frappe.db.sql(f"SELECT * FROM `tabJournal Entry Account` where account='{jv_ac_name}' AND reference_name = '{doc_name}' ", as_dict=True)


    if parent_payment_entry:
        for each_parent in parent_payment_entry:
            payment_entry = frappe.get_doc('Payment Entry', each_parent)
            if payment_entry.status =='Submitted':
                child_table.append({'entry_type': 'Payment Entry', 'entry_name': payment_entry.name, 'settled_amount': payment_entry.paid_amount, 'tds_amount': payment_entry.custom_tds_amount, 'disallowance_amount':
                payment_entry.custom_disallowed_amount,'writeoff_amount':0, 'allocated_amount':  payment_entry.total_allocated_amount, 'utr_number':  payment_entry.reference_no, 'utr_date':  payment_entry.reference_date,
                'created_date':payment_entry.posting_date
                  })

    if jv:
        for entry in range(len(jv)):
            jv_entry = jv[entry]
            entry_type = jv_entry.parent.split('-')[1]
            tds,dis,wo=0,0,0
            if entry_type == "RND":
                continue
            elif entry_type == "TDS":
                tds=jv[entry]['credit']
            elif entry_type == 'DIS':
                dis=jv[entry]['credit']
            elif entry_type == 'WO':
                wo=jv[entry]['credit']
            jv_doc=frappe.get_doc('Journal Entry',jv[entry]['parent'])
            child_table.append({'entry_type': 'Journal Entry', 'entry_name': jv_doc.name,
                                'settled_amount': 0,
                                'tds_amount': tds, 'disallowance_amount':dis,'writeoff_amount':wo,
                                'allocated_amount': jv_doc.total_credit,
                                'utr_number': "", 'utr_date':jv_doc.posting_date,
                                'created_date': ""
                                })

    matcher_list = []
    matcher = frappe.db.sql(f"SELECT * FROM `tabMatcher` where sales_invoice ='{doc_name}' AND status = 'Processed' ", as_dict=True)
    if matcher:
        for matcher_doc in matcher:
            if matcher_doc.settlement_advice:
                matcher_link_value_sa = matcher_doc.settlement_advice
                matcher_link_value_cb = "No Match"
            elif matcher_doc.claimbook:
                matcher_link_value_cb = matcher_doc.claimbook
                matcher_link_value_sa = "No Match"

            matcher_list.append({'matcher_id': matcher_doc.name,
                                 'matcher_logic': matcher_doc.match_logic,
                                 'settlement_advice':matcher_link_value_sa,
                                 'claimbook': matcher_link_value_cb
                                 })

    return child_table, matcher_list