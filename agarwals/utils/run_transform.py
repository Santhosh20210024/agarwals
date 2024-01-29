from agarwals.utils.transformer import BillTransformer,ClaimbookTransformer,BankTransformer
import frappe
from agarwals.utils.record_mapper import ClaimBookMapper, FinalDetailsMapper

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
def map_claim_book_records():
    try:
        ClaimBookMapper().enqeue_job()
    except Exception as e:
        frappe.throw(e)

@frappe.whitelist()
def map_final_details():
    try:
        FinalDetailsMapper().enqeue_job()
    except Exception as e:
        frappe.throw(e)