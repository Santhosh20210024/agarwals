import frappe
from datetime import date

ERROR_LOG = { 
    'S100': 'Settlement Advice Already Exist',
    'S101': 'UTR and claim Id is Mandaory',
    'S102': 'Settled amount is Mandatory',
    'S103': 'UTR must in Non-Exponential Formate',
    'S104': 'System Error',
    'S105': 'Amount Should Not Be Negative'
}

def log_error(doctype_name, error_doc, error_message):
    error_log = frappe.new_doc('Error Record Log')
    error_log.set('doctype_name', doctype_name)
    error_log.set('reference_name', error_doc.name)
    error_log.set('error_message', error_message)
    error_log.save()
    error_doc.status = "Error"
    if "Duplicate entry" in str(error_message):
        error_doc.remarks = ERROR_LOG['S100']
        error_doc.error_code = 'S100'
    else:
        error_doc.remarks = ERROR_LOG['S104']
        error_doc.error_code = 'S104'
    error_doc.save(ignore_permissions=True)
    frappe.db.commit()

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
        log_error('Settlement Advice Staging',doc_to_insert,e)


def settlement_advice_staging(advices):
     for advice in advices:
            try:
                advice_staging_doc=frappe.get_doc('Settlement Advice Staging',advice[0])
                advice_staging_doc.date = date.today(),
                if advice_staging_doc.status == "Error" and advice_staging_doc.retry==0:
                    continue
                advice_staging_doc.retry=0
                if advice_staging_doc.status == "Open" and (advice_staging_doc.final_utr_number == "0" or advice_staging_doc.final_utr_number is None  or advice_staging_doc.claim_id =="0" or advice_staging_doc.utr_number is None):
                    advice_staging_doc.status = "Error"
                    advice_staging_doc.remarks =ERROR_LOG["S101"] 
                    advice_staging_doc.error_code = "S101"
                    advice_staging_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    continue
                if advice_staging_doc.settled_amount is None or advice_staging_doc.settled_amount == 0:
                    advice_staging_doc.status = "Error"
                    advice_staging_doc.remarks =ERROR_LOG["S102"] 
                    advice_staging_doc.error_code = "S102"
                    advice_staging_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    continue
                if advice_staging_doc.settled_amount < 0 or advice_staging_doc.tds_amount < 0 or advice_staging_doc.disallowed_amount < 0:
                    advice_staging_doc.status = "Error"
                    advice_staging_doc.remarks =ERROR_LOG["S105"]
                    advice_staging_doc.error_code = "S105"
                    advice_staging_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    continue
                if "e+" in advice_staging_doc.final_utr_number.lower() or "e+" in advice_staging_doc.utr_number.lower():
                    advice_staging_doc.status = "Error"
                    advice_staging_doc.remarks =ERROR_LOG["S103"] 
                    advice_staging_doc.error_code = "S103"
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
                log_error('Settlement Advice Staging',advice_staging_doc,e)
                continue
        

@frappe.whitelist()
def process():
        advices_list = frappe.db.sql("SELECT name FROM `tabSettlement Advice Staging` tsas WHERE status = 'Open' OR (status = 'Error' AND retry=1);",as_list=True)
        settlement_advice_staging(advices_list)
        # n = 1000
        # for i in range(0, len(advices_list), n):
        #       frappe.enqueue(settlement_advice_staging, queue='long', is_async=True, job_name="settlement advice staging", timeout=25000,
        #                advices = advices_list[i:i + n])
        
        
