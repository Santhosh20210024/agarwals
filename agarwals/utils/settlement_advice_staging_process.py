import frappe

def insert_record_in_settlement_advice(doc_to_insert):
    try:
        frappe.get_doc({
            "doctype": "Settlement Advice",
            "paid_date": doc_to_insert.paid_date,
            "utr_number": doc_to_insert.utr_number,
            "bill_no": doc_to_insert.bill_number,
            "claim_id": doc_to_insert.claim_id,
            "claim_amount": doc_to_insert.claim_amount,
            "settled_amount": doc_to_insert.settled_amount,
            "tds_amount": doc_to_insert.tds_amount,
            "source": "TPA",
            "status": "Open",
        }).insert(ignore_permissions=True)
        doc_to_insert.status = "Processed"
        doc_to_insert.save(ignore_permissions=True)
    except Exception as e:
        print(e)
        doc_to_insert.status = "Error"
        doc_to_insert.remarks = str(e)
        doc_to_insert.save(ignore_permissions=True)
    frappe.db.commit()
        

@frappe.whitelist()
def process():
    try:
        for advice in frappe.get_all('Settlement Advice Staging',filters = {'status' : ['!=', 'Processed']}, fields = "*" ):
            advice_staging_doc=frappe.get_doc('Settlement Advice Staging',advice.name)
            if advice_staging_doc.status == "Error" and advice_staging_doc.retry==0:
                continue
            if advice_staging_doc.status == "Open" and (advice_staging_doc.utr_number == None or advice_staging_doc.claim_id == None):
                advice_staging_doc.status = "Error"
                advice_staging_doc.remarks = "UTR and claim id should not be null"
                advice_staging_doc.save(ignore_permissions=True)
                frappe.db.commit()
                continue
            
            insert_record_in_settlement_advice(advice_staging_doc)
        return "Success"
    except Exception as e:
        return e
        
        