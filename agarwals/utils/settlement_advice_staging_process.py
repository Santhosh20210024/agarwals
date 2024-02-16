import frappe
from datetime import date


def log_error(doctype_name, reference_name, error_message):
    error_log = frappe.new_doc('Error Record Log')
    error_log.set('doctype_name', doctype_name)
    error_log.set('reference_name', reference_name)
    error_log.set('error_message', error_message)
    error_log.save()

def insert_record_in_settlement_advice(doc_to_insert):
    try:
        settlement_advices = frappe.get_list("Settlement Advice", filters={
            'utr_number': doc_to_insert.utr_number, 'claim_id':doc_to_insert.claim_id, 'status': "Error"})
        print(settlement_advices)
        if len(settlement_advices) > 0 and doc_to_insert.retry == 1:
            name = doc_to_insert.utr_number + "-" + doc_to_insert.claim_id + "-" + str(len(settlement_advices))
        else:
            name = doc_to_insert.utr_number + "-" + doc_to_insert.claim_id
        frappe.get_doc({
            "doctype": "Settlement Advice",
            "name": name,
            "claim_id": doc_to_insert.claim_id,
            "bill_no":doc_to_insert.bill_number,
            "utr_number": doc_to_insert.utr_number,
            "final_utr_number":doc_to_insert.final_utr_number,
            "claim_amount": doc_to_insert.claim_amount,
            "disallowed_amount":doc_to_insert.disallowed_amount,
            "payers_remark":doc_to_insert.payers_remark,
            "tds_amount": doc_to_insert.tds_amount,
            "settled_amount": doc_to_insert.settled_amount,
            "paid_date": doc_to_insert.paid_date,
            "source_file":doc_to_insert.source,
            "source": "TPA",
            "status": "Open",   
        }).insert(ignore_permissions=True)
        doc_to_insert.status = "Processed"
        doc_to_insert.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        log_error('Settlement Advice Staging',doc_to_insert.name,e)
        doc_to_insert.status = "Error"
        doc_to_insert.remarks = str(e)
        doc_to_insert.save(ignore_permissions=True)
        frappe.db.commit()
        

@frappe.whitelist()
def process():
        for advice in frappe.get_all('Settlement Advice Staging',filters = {'status' : ['!=', 'Processed'],'retry':['!=', 0]}, fields = "*" ):
            try:
                advice_staging_doc=frappe.get_doc('Settlement Advice Staging',advice.name)
                advice_staging_doc.date = date.today(),
                if advice_staging_doc.status == "Error" and advice_staging_doc.retry==0:
                    continue
                advice_staging_doc.retry=0
                if advice_staging_doc.status == "Open" and (advice_staging_doc.final_utr_number == "0" or advice_staging_doc.final_utr_number is None  or advice_staging_doc.claim_id =="0" or advice_staging_doc.utr_number is None):
                    advice_staging_doc.status = "Error"
                    advice_staging_doc.remarks = "UTR and claim id should not be null,"
                    advice_staging_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    continue
                if advice_staging_doc.settled_amount is None or advice_staging_doc.settled_amount == 0:
                    advice_staging_doc.status = "Error"
                    advice_staging_doc.remarks = "No Settled amount,"
                    advice_staging_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    continue
                if "e+" in advice_staging_doc.final_utr_number.lower() or "e+" in advice_staging_doc.utr_number.lower():
                    advice_staging_doc.status = "Error"
                    advice_staging_doc.remarks = "utr number should not be in exponential formate,"
                    advice_staging_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    continue
                advice_staging_doc.claim_id=advice_staging_doc.claim_id.replace(".0","")
                advice_staging_doc.final_utr_number = advice_staging_doc.final_utr_number.replace(".0","")
                advice_staging_doc.utr_number = advice_staging_doc.utr_number.replace(".0","")
                advice_staging_doc.save(ignore_permissions=True)
                frappe.db.commit()
                insert_record_in_settlement_advice(advice_staging_doc)
            except Exception as e:
                log_error('Settlement Advice Staging',advice.name,e)
                advice_staging_doc.status = "Error"
                advice_staging_doc.remarks = e
                advice_staging_doc.save(ignore_permissions=True)
                frappe.db.commit()
                continue
        return "Success"
        
        