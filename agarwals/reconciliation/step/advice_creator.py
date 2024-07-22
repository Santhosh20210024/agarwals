import frappe
from datetime import date

from agarwals.agarwals.doctype import file_records
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic

ERROR_LOG = { 
    'S100': 'Settlement Advice Already Exist',
    'S101': 'UTR and claim Id is Mandatory',
    'S102': 'Settled amount is Mandatory',
    'S103': 'UTR must in Non-Exponential Formate',
    'S104': 'System Error',
    'S105': 'Amount Should Not Be Negative',
    'S106': 'Already Processed Cannot Be Updated'
}


def update_error(error_doc,error_code):
    error_doc.status = 'Error'
    error_doc.remarks = ERROR_LOG[error_code]
    error_doc.error_code = error_code
    error_doc.save(ignore_permissions=True)
    frappe.db.commit()

def log_error(doctype_name, error_doc, error_message):
    error_log = frappe.new_doc('Error Record Log')
    error_log.set('doctype_name', doctype_name)
    if error_doc:
        error_log.set('reference_name', error_doc.name)
    error_log.set('error_message', error_message)
    error_log.save()
    update_error(error_doc,'S104')


def update_sa_status(doctype,doc_name,status):
    doc = frappe.get_doc(doctype,doc_name)
    doc.status = status
    doc.save()

def insert_record_in_settlement_advice(doc_to_insert):
    settlement_advices = frappe.get_list("Settlement Advice", filters={
        'utr_number': doc_to_insert.utr_number, 'claim_id': doc_to_insert.claim_id, 'status': "Error"})
    if len(settlement_advices) > 0 and doc_to_insert.retry == 1:
        name = doc_to_insert.utr_number + "-" + doc_to_insert.claim_id + "-" + str(len(settlement_advices))
    else:
        name = doc_to_insert.utr_number + "-" + doc_to_insert.claim_id
    data = {
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
        "file_upload": doc_to_insert.file_upload,
        "transform": doc_to_insert.transform,
        "index": doc_to_insert.index,
        "source": "TPA",
        "status": "Open",
    }
    try:
        sa_doc = frappe.get_doc(data).insert(ignore_permissions=True)
        update_sa_status('Settlement Advice Staging',doc_to_insert.name,'Processed')
    except Exception as e:
        if "Duplicate entry" in str(e):
            sa_doc = frappe.get_doc('Settlement Advice',name)
            if sa_doc.tds_amount == doc_to_insert.tds_amount and sa_doc.settled_amount == doc_to_insert.settled_amount and sa_doc.disallowed_amount==doc_to_insert.disallowed_amount:
                update_error(doc_to_insert,'S100')
                return
            if sa_doc.status in ['Partially Processed','Fully Processed','Warning']:
                update_error(doc_to_insert,'S106')
                return
            sa_doc.update(data)
            sa_doc.save()
            update_sa_status('Settlement Advice Staging', doc_to_insert.name, 'Processed')
        else:
            log_error('Settlement Advice Staging', doc_to_insert, e)

def settlement_advice_staging(advices,chunk_doc=None):
    chunk.update_status(chunk_doc, "InProgress")
    try:
        for advice in advices:
                try:
                    advice_staging_doc=frappe.get_doc('Settlement Advice Staging',advice[0])
                    advice_staging_doc.date = date.today(),
                    if advice_staging_doc.status == "Error" and advice_staging_doc.retry==0:
                        continue
                    advice_staging_doc.retry=0
                    if advice_staging_doc.status == "Open" and (advice_staging_doc.final_utr_number == "0" or advice_staging_doc.final_utr_number is None  or advice_staging_doc.claim_id =="0" or advice_staging_doc.utr_number is None):
                        update_error(advice_staging_doc, 'S101')
                        continue
                    if advice_staging_doc.settled_amount is None or advice_staging_doc.settled_amount == 0:
                        update_error(advice_staging_doc, 'S102')
                        continue
                    if advice_staging_doc.settled_amount < 0 or advice_staging_doc.tds_amount < 0 or advice_staging_doc.disallowed_amount < 0:
                        update_error(advice_staging_doc, 'S105')
                        continue
                    if "e+" in advice_staging_doc.final_utr_number.lower() or "e+" in advice_staging_doc.utr_number.lower():
                        update_error(advice_staging_doc, 'S103')
                        continue
                    advice_staging_doc.claim_id=advice_staging_doc.claim_id.replace(".0","")
                    advice_staging_doc.final_utr_number = advice_staging_doc.final_utr_number.replace(".0","")
                    advice_staging_doc.utr_number = advice_staging_doc.utr_number.replace(".0","")
                    advice_staging_doc.save(ignore_permissions=True)
                    insert_record_in_settlement_advice(advice_staging_doc)
                    frappe.db.commit()
                except Exception as e:
                    log_error('Settlement Advice Staging',advice_staging_doc,e)
                    continue
        chunk.update_status(chunk_doc, "Processed")
    except Exception as e:
        log_error('Settlement Advice Staging',None , e)
        chunk.update_status(chunk_doc, "Error")


@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    try:
        advices_list = frappe.db.sql("SELECT name FROM `tabSettlement Advice Staging` tsas WHERE status = 'Open' OR (status = 'Error' AND retry=1);",as_list=True)
        n = int(args["chunk_size"])
        if advices_list:
            for i in range(0, len(advices_list), n):
                chunk_doc=chunk.create_chunk(args["step_id"])
                frappe.enqueue(settlement_advice_staging, queue=args["queue"], is_async=True, job_name="settlement advice staging", timeout=25000,
                           advices = advices_list[i:i + n],chunk_doc=chunk_doc)
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
    except Exception as e:
        from agarwals.utils.error_handler import log_error
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')