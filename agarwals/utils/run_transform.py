# from transformer import BillTransformer,ClaimbookTransformer,BankTransformer,SettlementTransformer
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