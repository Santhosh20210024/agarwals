import frappe

def insert_record_in_settlement_advice(doc_to_insert):
    try:
        settlement_advices = frappe.get_list("Settlement Advice", filters={'name':str(doc_to_insert.utr_number) + str(doc_to_insert.claim_id), 'status':"Error"})
        if len(settlement_advices) > 0:
            name = doc_to_insert.utr_number + doc_to_insert.claim_id
        else:
            name = doc_to_insert.utr_number + doc_to_insert.claim_id + "-" + str(len(settlement_advices))

        print(name)
        settlement_advice = frappe.new_doc("Settlement Advice")
        settlement_advice.set("name",name)
        settlement_advice.set("paid_date", doc_to_insert.paid_date)
        settlement_advice.set("utr_number", doc_to_insert.utr_number)
        settlement_advice.set("bill_no", doc_to_insert.bill_number)
        settlement_advice.set("claim_id", doc_to_insert.claim_id)
        settlement_advice.set("claim_amount", doc_to_insert.claim_amount)
        settlement_advice.set("settled_amount", doc_to_insert.settled_amount)
        settlement_advice.set("tds_amount",doc_to_insert.tds_amount)
        settlement_advice.set("source","TPA")
        settlement_advice.set("status","Open")
        settlement_advice.save()
        doc_to_insert.status = "Processed"
        doc_to_insert.retry = 0
        doc_to_insert.save(ignore_permissions=True)
        print("Created")
        frappe.db.commit()
        
    except Exception as e:
        print(e)
        doc_to_insert.status = "Error"
        doc_to_insert.remarks = str(e)
        doc_to_insert.retry = 0
        doc_to_insert.save(ignore_permissions=True)
        frappe.db.commit()
        

@frappe.whitelist()
def process():
    for advice in frappe.get_all('Settlement Advice Stagging',filters = {'status' : ['!=', 'Processed']}, fields = "*" ):
        advice_stagging_doc=frappe.get_doc('Settlement Advice Stagging',advice.name)
        if advice_stagging_doc.status == "Error" and advice_stagging_doc.retry==0:
            continue
        if advice_stagging_doc.utr_number == None or advice_stagging_doc.claim_id == None:
            advice_stagging_doc.status = "Error"
            advice_stagging_doc.remarks = "UTR and claim id should not be null"
            advice_stagging_doc.save(ignore_permissions=True)
            frappe.db.commit()
            continue
        
        insert_record_in_settlement_advice(advice_stagging_doc)
        
        