import frappe
from datetime import date
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error as error_handler

ERROR_LOG = { 
    'S100': 'Settlement Advice Already Exist',
    'S101': 'UTR and claim Id is Mandatory',
    'S102': 'Settled amount is Mandatory',
    'S103': 'UTR must in Non-Exponential Formate',
    'S104': 'System Error',
    'S105': 'Amount Should Not Be Negative',
    'S106': 'Already Processed Cannot Be Updated'
}
staging_doc = 'Settlement Advice Staging'

def update_error(error_doc,error_code):
    error_doc.status = 'Error'
    error_doc.remarks = ERROR_LOG[error_code]
    error_doc.error_code = error_code
    return error_doc

def log_error(doctype_name, error_doc, error_message):
    error_log = error_handler(error=error_message, doc=doctype_name, doc_name=error_doc)
    if error_doc:
        error_log.set('reference_name', error_doc.name)
        error_log.save()
        return update_error(error_doc,'S104')

def update_processed_status(doc_to_update):
    doc_to_update.status = 'Processed'
    return doc_to_update

def create_settlement_advice_doc(doc_to_insert):
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
            "cl_number": doc_to_insert.cl_number,
            "bill_no":doc_to_insert.bill_number,
            "mrn":doc_to_insert.mrn,
            "utr_number": doc_to_insert.utr_number,
            "final_utr_number":doc_to_insert.final_utr_number,
            "paid_date": doc_to_insert.paid_date,
            "insurance_company": doc_to_insert.insurance_company,
            "patient_name": doc_to_insert.patient_name,
            "insurance_policy_number": doc_to_insert.insurance_policy_number,
            "date_of_admission": doc_to_insert.date_of_admission,
            "date_of_discharge": doc_to_insert.date_of_discharge,
            "hospital_name": doc_to_insert.hospital_name,
            "bank_account_number": doc_to_insert.bank_account_number,
            "bank_name": doc_to_insert.bank_name,
            "bank_branch": doc_to_insert.bank_branch,
            "claim_amount": doc_to_insert.claim_amount,
            "settled_amount": doc_to_insert.settled_amount,
            "tds_amount": doc_to_insert.tds_amount,
            "disallowed_amount":doc_to_insert.disallowed_amount,
            "payers_remark":doc_to_insert.payers_remark,
            "file_upload": doc_to_insert.file_upload,
            "transform": doc_to_insert.transform,
            "index": doc_to_insert.index,
            "staging": doc_to_insert.name,
            "status": "Open",
        }
    try:
        sa_doc = frappe.get_doc(data).insert(ignore_permissions=True)
        return update_processed_status(doc_to_insert)
    except Exception as e:
        if "Duplicate entry" in str(e):
            sa_doc = frappe.get_doc('Settlement Advice', name)
            if float(sa_doc.tds_amount) == float(doc_to_insert.tds_amount) and float(sa_doc.settled_amount) == float(doc_to_insert.settled_amount) and float(sa_doc.disallowed_amount) == float(doc_to_insert.disallowed_amount):
                return update_error(doc_to_insert, 'S100')
            if sa_doc.status == 'Warning' and sa_doc.remark == "Claim Amount is lesser than the sum of Settled Amount, TDS Amount and Disallowance Amount.":
                sa_doc.update(data)
                sa_doc.save()
                return update_processed_status(doc_to_insert)
            return update_error(doc_to_insert, 'S106')
        else:
            raise Exception(e)

def validate_advice(advice_staging_doc):
    if advice_staging_doc.status == "Error" and advice_staging_doc.retry == 0:
        return False
    advice_staging_doc.retry = 0
    if advice_staging_doc.status == "Open" and (
            advice_staging_doc.final_utr_number == "0" or advice_staging_doc.final_utr_number is None or advice_staging_doc.claim_id == "0" or advice_staging_doc.utr_number is None):
        return update_error(advice_staging_doc, "S101"), False
    if advice_staging_doc.settled_amount is None or float(advice_staging_doc.settled_amount) == 0:
        return update_error(advice_staging_doc, "S102"), False
    if float(advice_staging_doc.settled_amount) < 0 or float(advice_staging_doc.tds_amount) < 0 or float(advice_staging_doc.disallowed_amount) < 0:
        return update_error(advice_staging_doc, "S105"), False
    if "e+" in advice_staging_doc.final_utr_number.lower() or "e+" in advice_staging_doc.utr_number.lower():
        return update_error(advice_staging_doc, "S103"), False
    return advice_staging_doc, True

def clean_sa_data(data):
    return data.replace(".0","").strip() if data else data

def create_settlement_advices(advices, chunk_doc):
    chunk.update_status(chunk_doc, "InProgress")
    chunk_status = "Processed"
    try:
        for advice in advices:
            advice_staging_doc=frappe.get_doc(staging_doc,advice[0])
            try:
                advice_staging_doc, flag = validate_advice(advice_staging_doc)
                if not flag:
                    continue
                advice_staging_doc.date = date.today()
                advice_staging_doc.claim_id= clean_sa_data(advice_staging_doc.claim_id)
                advice_staging_doc.final_utr_number = clean_sa_data(advice_staging_doc.final_utr_number)
                advice_staging_doc.utr_number = clean_sa_data(advice_staging_doc.utr_number)
                advice_staging_doc = create_settlement_advice_doc(advice_staging_doc)
            except Exception as e:
                advice_staging_doc = log_error(staging_doc, advice_staging_doc,e)
                continue
            finally:
                advice_staging_doc.save(ignore_permissions=True)
                frappe.db.commit()
    except Exception as e:
        chunk_status = "Error"
        log_error(staging_doc, None, e)
    finally:
        chunk.update_status(chunk_doc, chunk_status)

@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    try:
        advices_list = frappe.db.sql("SELECT name FROM `tabSettlement Advice Staging` tsas WHERE status = 'Open' OR (status = 'Error' AND retry=1);",as_list=True)
        n = int(args["chunk_size"])
        if advices_list:
            for i in range(0, len(advices_list), n):
                chunk_doc=chunk.create_chunk(args["step_id"])
                # create_settlement_advices(advices = advices_list[i:i + n], chunk_doc=chunk_doc)
                frappe.enqueue(create_settlement_advices, queue=args["queue"], is_async=True, job_name="Advice Creation", timeout=25000,
                               advices = advices_list[i:i + n], chunk_doc=chunk_doc)
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
    except Exception as e:
        from agarwals.utils.error_handler import log_error
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')