from agarwals.reconciliation.step.transform.transformer import BillTransformer, ClaimbookTransformer, BankTransformer, AdjustmentTransformer, WritebackTransformer, WriteoffTransformer,BankBulkTransformer
from agarwals.reconciliation.step.transform import settlement_advice

def get_transformer(type):
    try:
        if type == "debtors":
            return BillTransformer()
        elif type == "claimbook":
            return ClaimbookTransformer()
        elif type == "Settlement":
            return settlement_advice
        elif type == "transaction":
            return BankTransformer()
        elif type == "adjustment":
            return AdjustmentTransformer()
        elif type == "writeback":
            return WritebackTransformer()
        elif type == "writeoff":
            return WriteoffTransformer()
        elif type == "bank_transaction":
            return BankBulkTransformer()
    except Exception as e:
       return e