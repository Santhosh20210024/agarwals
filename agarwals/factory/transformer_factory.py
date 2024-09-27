from agarwals.reconciliation.step.transform.bill_transformer import BillTransformer
from agarwals.reconciliation.step.transform.claimbook_transformer import ClaimbookTransformer
from agarwals.reconciliation.step.transform.bank_transformer import BankTransformer
from agarwals.reconciliation.step.transform.adjustment_transformer import AdjustmentTransformer
from agarwals.reconciliation.step.transform.writeback_transformer import WritebackTransformer
from agarwals.reconciliation.step.transform.writeoff_transformer import WriteoffTransformer
from agarwals.reconciliation.step.transform.bank_transformer import BankBulkTransformer
from agarwals.reconciliation.step.transform.advice_transformer import AdviceTransformer
from agarwals.reconciliation.step.transform.closing_balance_transformer import ClosingBalanceTransformer
from agarwals.reconciliation.step.transform.tpa_credentials_transformer import TpaCredentialsTransformer

def get_transformer(type):
    try:
        if type == "debtors":
            return BillTransformer()
        elif type == "claimbook":
            return ClaimbookTransformer()
        elif type == "Settlement":
            return AdviceTransformer()
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
        elif type =="closing_balance":
            return ClosingBalanceTransformer()
        elif type == "tpa_credentails":
            return TpaCredentialsTransformer()

    except Exception as e:
       return e