from agarwals.utils.transformer import BillTransformer,ClaimbookTransformer,BankTransformer
from agarwals.utils.payment_entry_creator import PaymentEntryCreator
import frappe

@frappe.whitelist()
def run_transform_process(type):
    if type == "debtors":
        try:
            BillTransformer().process()
            return "Success"
        except Exception as e:
            return e
    elif type == "claimbook":
        try:
            ClaimbookTransformer().process()
            return "Success"
        except Exception as e:
            return e
    # elif type =="Settlement":
    #     try:
    #         SettlementTransformer().process()
    #         return "Success"
    #     except Exception as e:
    #         return e
    elif type =="transaction":
        try:
            BankTransformer().process()
            return "Success"
        except Exception as e:
            return e

@frappe.whitelist()
def run_payment_entry():
    bank_transaction_records = frappe.db.sql(
        "SELECT name, bank_account, reference_number, date FROM `tabBank Transaction` WHERE status IN ('Pending','Unreconciled')  AND LENGTH(reference_number) > 4 AND deposit > 10 ORDER BY unallocated_amount DESC",
        as_dict=True)
    claim_records = frappe.db.sql(
        "SELECT name, al_number, cl_number, custom_raw_bill_number, insurance_company_name FROM `tabClaimBook`",
        as_dict=True)
    bill_records = frappe.db.sql("SELECT name, claim_id FROM `tabBill` WHERE status != 'CANCELLED'",
                                      as_dict=True)
    settlement_advice_records = frappe.db.sql(
        "SELECT name, utr_number, final_utr_number, settled_amount, tds_amount, disallowed_amount FROM `tabSettlement Advice` WHERE status IN ('Open','Error','Warning')",
        as_dict=True)
    batch_number = 0
    n = 2000
    for i in range(0, len(bank_transaction_records), n):
        batch_number = batch_number + 1
        frappe.enqueue(PaymentEntryCreator(claim_records,bill_records,settlement_advice_records).process, queue='myqueue', is_async=True, job_name="Batch" + str(batch_number), timeout=25000,
                       bank_transaction_records=bank_transaction_records[i:i + n])
        print('Job Enqueued ', batch_number)