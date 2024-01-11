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
        log_error('Settlement Advice Staging',doc_to_insert.name,e)
        doc_to_insert.status = "Error"
        doc_to_insert.remarks = str(e)
        doc_to_insert.save(ignore_permissions=True)
        frappe.db.commit()
        

@frappe.whitelist()
def process():
        for advice in frappe.get_all('Settlement Advice Staging',filters = {'status' : ['!=', 'Processed']}, fields = "*" ):
            try:
                advice_staging_doc=frappe.get_doc('Settlement Advice Staging',advice.name)
                advice_staging_doc.date = date.today(),
                if advice_staging_doc.status == "Error" and advice_staging_doc.retry==0:
                    continue
                if advice_staging_doc.status == "Open" and (advice_staging_doc.utr_number == "0" or advice_staging_doc.utr_number is None  or advice_staging_doc.claim_id =="0" or advice_staging_doc.utr_number is None):
                    advice_staging_doc.status = "Error"
                    advice_staging_doc.remarks = "UTR and claim id should not be null"
                    advice_staging_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    continue
                
                insert_record_in_settlement_advice(advice_staging_doc)
            except Exception as e:
                log_error('Settlement Advice Staging',advice.name,e)
                advice_staging_doc.status = "Error"
                advice_staging_doc.remarks = e
                advice_staging_doc.save(ignore_permissions=True)
                frappe.db.commit()
                continue
        return "Success"
        
        