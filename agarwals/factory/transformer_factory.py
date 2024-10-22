from agarwals.reconciliation.step.transform.bill_transformer import BillTransformer
from agarwals.reconciliation.step.transform.claimbook_transformer import ClaimbookTransformer
from agarwals.reconciliation.step.transform.bank_transformer import BankTransformer
from agarwals.reconciliation.step.transform.adjustment_transformer import AdjustmentTransformer
from agarwals.reconciliation.step.transform.writeback_transformer import WritebackTransformer
from agarwals.reconciliation.step.transform.writeoff_transformer import WriteoffTransformer
from agarwals.reconciliation.step.transform.bank_transformer import BankBulkTransformer
from agarwals.reconciliation.step.transform.advice_transformer import AdviceTransformer
from agarwals.reconciliation.step.transform.closing_balance_transformer import ClosingBalanceTransformer
from agarwals.reconciliation.step.transform.bank_update_transformer import BankUpdateTransformer
from agarwals.reconciliation.step.transform.tpa_credentials_transformer import TpaCredentialsTransformer
from agarwals.reconciliation.step.transform.bill_entry_transformer import BillEntryTransformer


def get_transformer(transformer_type: str):
    transformer_type = transformer_type.lower()
    if transformer_type == "debtors":
        return BillTransformer()
    elif transformer_type == "claimbook":
        return ClaimbookTransformer()
    elif transformer_type == "settlement":
        return AdviceTransformer()
    elif transformer_type == "transaction":
        return BankTransformer()
    elif transformer_type == "adjustment":
        return AdjustmentTransformer()
    elif transformer_type == "writeback":
        return WritebackTransformer()
    elif transformer_type == "writeoff":
        return WriteoffTransformer()
    elif transformer_type == "bank_transaction":
        return BankBulkTransformer()
    elif transformer_type == "closing_balance":
        return ClosingBalanceTransformer()
    elif transformer_type == "tpa_credentails":
        return TpaCredentialsTransformer()
    elif transformer_type == "bill_entry":
        return BillEntryTransformer()
    elif transformer_type == "bank_update":
        return BankUpdateTransformer()
    else:
        raise NotImplementedError(f"Unable to find the transformer for the type {transformer_type}")