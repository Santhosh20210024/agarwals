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
    elif type =="Settlement":
        try:
            SettlementTransformer().process()
            return "Success"
        except Exception as e:
            return e
    elif type =="transaction":
        try:
            BankTransformer().process()
            return "Success"
        except Exception as e:
            return e

@frappe.whitelist()
def run_payment_entry():

    batch_number = 0
    n = int(frappe.get_single('Control Panel').payment_matching_chunk_size)
    match_logic = frappe.get_single('Control Panel').match_logic

    # Need to change as X00
    bank_transaction_records = frappe.db.sql(
        f"SELECT name, bank_account, reference_number, date FROM `tabBank Transaction`
          WHERE name in (select bank_transaction from `tabMatcher` where match_logic = {match_logic} and status is null )
          AND status IN ('Pending','Unreconciled')
          AND LENGTH(reference_number) > 4 AND deposit > 10 AND reference_number not like 'X0%'
          ORDER BY unallocated_amount DESC",
        as_dict=True
        )

    for i in range(0, len(bank_transaction_records), n):
        batch_number = batch_number + 1
        frappe.enqueue(PaymentEntryCreator().process, queue='long', is_async=True, job_name="Batch" + str(batch_number), timeout=25000,
                       bank_transaction_records = bank_transaction_records[i:i + n], match_logic = match_logic)