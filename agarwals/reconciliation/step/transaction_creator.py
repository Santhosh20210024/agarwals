import frappe
import traceback
from frappe.utils import today
from agarwals.agarwals.doctype import file_records
from tfs.orchestration import ChunkOrchestrator
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error, CGException
from agarwals.utils import DatabaseUtils
from agarwals.utils.fiscal_year_update import get_fiscal_year
from .. import BANK_TRANSACTION_STAGING_DOCTYPE, BANK_TRANSACTION_DOCTYPE, BANK_UPDATE_DOCTYPE
from agarwals.reconciliation.step.bank_transaction_processes.closing_balance_check import (
    ClosingBalance,
)
from agarwals.reconciliation.step.cancellator.cancellator import (
    PaymentDocumentCancellator,
)
from agarwals.reconciliation.step.cancellator.utils.matcher_cancellator import (
    MatcherCancellator,
)
from frappe.exceptions import ValidationError

STAGING_ERROR_LOG = {
    "E100": "Duplicate Reference Number",
    "E101": "Both Deposit and Withdrawn should not be zero",
    "E102": "Reference Number is invalid",
    "E103": "Previously processed and already Reconciled Bank Transaction",
    "E104": "Deposit Amount must exceed 1 Rupee",
    "E105": "System Error While Processing"
}

class BankStagingException(CGException):
    def __init__(self, method_name, error):
        super().__init__(method_name, error)

class BankStagingUtils():
    """
    BankStagingUtils: Contains utility functions for managing bank transaction processing and transaction creation.

    Methods:
        clear_transaction_and_files: Clears associated transactions and file records for a specified document.
        clear_files: Deletes file records linked to a reference number.
        clear_transactions: Cancels and deletes the bank transaction associated with a reference number.
        check_bt_exists: Verifies if a bank transaction exists for the staging document.
        get_reference_number: Retrieves the reference number from the staging document.
        _is_reference_number_valid: Validates that the reference number has sufficient length.
    """

    def is_bank_trasaction_payments_present(self, reference_number): 
        return bool(frappe.db.get_all("Bank Transaction Payments", filters={'parent': reference_number}))

    def clear_transaction_and_files(self, doc_name):
        self.clear_transactions(doc_name)
        self.clear_files(doc_name)

    def clear_files(self, reference_no):
        try:
            frappe.delete_doc("File Records", reference_no, ignore_permissions=True)
        except Exception as e:
            log_error(f"{reference_no} -> {e}", doc="Bank Transaction")
            return

    def clear_transactions(self, reference_no):
        try:
            if self.check_bt_exists(reference_no):
                frappe.get_doc(BANK_TRANSACTION_DOCTYPE, reference_no).cancel()
                frappe.delete_doc(BANK_TRANSACTION_DOCTYPE, reference_no, ignore_permissions=True)
        except Exception as e:
            raise BankStagingException("clear_transactions", f"{reference_no} -> {e}")
    
    def check_bt_exists(self, reference_number):
        return frappe.db.exists(BANK_TRANSACTION_DOCTYPE, reference_number)
    
    def get_reference_number(self, staging_doc):
        return staging_doc.update_reference_number or staging_doc.get(
            "reference_number"
        )

    def _is_reference_number_valid(self, reference_number):
        """Validates if the reference number has sufficient length after stripping zeros."""
        return len(reference_number.strip().lstrip("0")) > 3


class BankStagingValidator():
    """
    BankStagingValidator: Validates various aspects of the Bank Transaction Staging process.

    Methods:
        _validate: Orchestrates the core validation steps for the staging process.
        _is_payer_name_set: Ensures that both 'payer_name' and 'payer_group' are mapped in Bank Transaction Staging.
        _validate_closing_balance: Validates the closing balance if the 'check_closing_balance' setting is enabled in the Control Panel.
        is_naming_rule_set: Checks if a Document Naming Rule exists for a given doctype.
        _validate_naming_rule: Ensures that the naming rule is set for Bank Transaction Doctype.
    """

    def _validate(self):
        self._is_payer_name_set()
        self._validate_closing_balance()
        self._validate_naming_rule()
        self.is_open_bank_update_docs()
    
    def _is_payer_name_set(self):
        if bool(
            frappe.get_all(
                BANK_TRANSACTION_STAGING_DOCTYPE,
                or_filters={
                    "payer_name": ["is", "not set"],
                    "payer_group": ["is", "not set"],
                },
            )
        ):
            raise ValueError(
                "Payer name and Payer Group are not fully mapped in Bank Transaction Staging."
            )

    def _validate_closing_balance(self):
        control_panel = frappe.get_doc("Control Panel")
        if control_panel.check_closing_balance == 1:
            ClosingBalance().validate_balance()

    def _is_naming_rule_set(self, doctype):
        return bool(
            frappe.get_all("Document Naming Rule", 
                           filters={"document_type": doctype})
        )

    def _validate_naming_rule(self):
        if not self._is_naming_rule_set(BANK_TRANSACTION_DOCTYPE):
            raise ValidationError(
                "Document Naming Rule is not set for Bank Transaction Doctype."
            )
    
    def is_open_bank_update_docs(self):
        if(bool(frappe.get_all("Bank Update", filters={'status':'Open'}))):
            raise ValidationError(
                "Bank Update Documents are in open status. Process it before bank staging process."
            )

class WithdrawalIncidentCleanupHandler:
    """
    WithdrawalIncidentCleanupHandler: Manages cleanup of matcher records and payment documents for cancelled bank transactions.

    Methods:
        cleanup: Cleans up related 'Matcher' records and cancels payment documents for a cancelled bank transaction.
        get_matcher_list: Retrieves matcher records associated with a bank transaction.
    """

    def __init__(self, reference_no):
        self.reference_no = reference_no

    def cleanup(self):
        for matcher in self.get_matcher_list():
            PaymentDocumentCancellator().cancel_payment_documents(matcher["sales_invoice"])
            MatcherCancellator().delete_matcher(frappe.get_doc('Sales Invoice', matcher["sales_invoice"]), is_commit=False)
            frappe.db.commit()

    def get_matcher_list(self):
        return frappe.get_all(
            "Matcher",
            filters={"bank_transaction": self.reference_no},
            fields=["sales_invoice", "name"],
        )
        

class BankStagingWithdrawalHandler():
    """
    BankStagingWithdrawalHandler: Manages withdrawal incidents in bank transactions.

    Description:
    This class handles cases where two bank transactions share the same reference number: one for a deposit and another for a withdrawal. 
    It identifies these incidents, cancels the deposit transaction if it matches the withdrawal, and performs necessary cleanup tasks 
    such as removing payment entries and associated matcher records.

    Methods:
        _handle_withdrawal_incident: Retrieves the list of withdrawal transactions and processes each one.
        get_withdrawal_list: Queries for transactions with matching deposit and withdrawal records based on the reference number.
        compare_date: Compares two dates to determine if the first is less than or equal to the second.
        _process_withdrawal_incident: Handles the validation and cancellation of the deposit transaction if it corresponds to the withdrawal.
        _cancel_transaction: Cancels the bank transaction, removes payment entries, and performs cleanup of related records.
    """
    
    def _handle_withdrawal_incident(self):
        withdrawal_list = self.get_withdrawal_list()

        for item in withdrawal_list:
            self._process_withdrawal_incident(item)
    
    def compare_date(self, cr_date, dt_date):
        return cr_date <= dt_date

    def get_withdrawal_list(self):
        bank_transaction_staging = frappe.qb.DocType(BANK_TRANSACTION_STAGING_DOCTYPE)
        bank_transaction = frappe.qb.DocType(BANK_TRANSACTION_DOCTYPE)
        return (
            frappe.qb.from_(bank_transaction_staging)
            .inner_join(bank_transaction)
            .on(bank_transaction.name == bank_transaction_staging.reference_number
            )
            .where(
                (bank_transaction.status != "Cancelled")
                & (bank_transaction_staging.withdrawal != 0)
            )
            .select(
                bank_transaction_staging.reference_number,
                bank_transaction_staging.withdrawal,
                bank_transaction_staging.date,
            )
            .run(as_dict=True)
        )

    def _process_withdrawal_incident(self, withdrawal_item):
        bank_transaction_doc = frappe.get_doc(
            BANK_TRANSACTION_DOCTYPE, withdrawal_item.get("reference_number")
        )
        allocated_amount = bank_transaction_doc.allocated_amount
        try:
            evaluate_amount = (bank_transaction_doc.deposit == withdrawal_item.get("withdrawal"))
            evaluate_date = self.compare_date(bank_transaction_doc.date, withdrawal_item.get("date"))
            if (bank_transaction_doc and evaluate_amount and evaluate_date):
                    self._cancel_transaction(bank_transaction_doc, allocated_amount)
        except Exception as e:
            raise BankStagingException("_process_withdrawal_incident", f"{bank_transaction_doc.name} -> {e}")

    def _cancel_transaction(self, bank_transaction_doc, allocated_amount):
        if allocated_amount != 0:
            cleanup_handler = WithdrawalIncidentCleanupHandler(bank_transaction_doc.name)
            cleanup_handler.cleanup()
        
        bank_transaction_doc = frappe.get_doc(BANK_TRANSACTION_DOCTYPE, bank_transaction_doc.name)
        bank_transaction_doc.add_comment(
            text="Bank Transaction cancelled due to withdrawal incident"
        )
        bank_transaction_doc.cancel()
        frappe.db.commit()


class BankStagingProcessInitiator(BankStagingValidator, BankStagingWithdrawalHandler):
    """
    BankStagingProcessInitiator: Manages the initiation and processing of bank transaction staging.

    Methods:
        _tag_skipped: Updates the staging status to "Skipped" for transactions based on withdrawal and tagging conditions.
        get_transactions_with_filters: Retrieves transactions from the staging table using specified filters and fields.
        _get_valid_transactions: Compiles a list of valid transactions based on predefined filters.
        _start_process: Initiates chunk processing of valid transactions, orchestrating batch tasks.
        _batch_process: Processes a batch of staging transactions by invoking `_process` from `StagingProcess`.
        initialize: Validates the process, handles withdrawal incidents, and starts processing valid transactions, returning the overall status.
    """
    def __init__(self):
        self.TAG = "Credit Payment"

    def _tag_skipped(self):
        bank_transaction_staging = frappe.qb.DocType(BANK_TRANSACTION_STAGING_DOCTYPE)
        frappe.qb.update(bank_transaction_staging).set(
            bank_transaction_staging.staging_status, "Skipped"
        ).where(
            (
                (bank_transaction_staging.withdrawal != 0.000000000)
                | (bank_transaction_staging.tag.isnull())
            )
            & (bank_transaction_staging.staging_status == "Open")
        ).run()

        frappe.db.commit()

    def get_transactions_with_filters(self, filters):
        return frappe.get_all(BANK_TRANSACTION_STAGING_DOCTYPE, filters=filters, fields=["name", "staging_status", "update_reference_number", "retry", "is_manual"])

    def process_manual(self, transactions = None): # Need to test
        if not transactions:
            transactions = self.get_transactions_with_filters({"is_manual": 1, "staging_status": ["in", ["Open", "Skipped"]]})
        for transaction in transactions:
            bank_trans_doc = frappe.get_doc(BANK_TRANSACTION_STAGING_DOCTYPE, transaction["name"])
            if bank_trans_doc.based_on != 'Insurance Pattern':
                bank_trans_doc.based_on = 'Manual'
            bank_trans_doc.staging_status = 'Open'
            bank_trans_doc.tag = self.TAG
            bank_trans_doc.save()
        frappe.db.commit()

    def _get_valid_transactions(self):
        valid_transactions = list()
        filters_list = [
            {"tag": self.TAG, "staging_status": "Open"},
            {"tag": self.TAG, "staging_status": ["in", ["Warning","Processed"]], "update_reference_number": ['is', 'set'], "retry": 1},
        ]
        self.process_manual()
        for filters in filters_list:
            valid_transactions.extend(self.get_transactions_with_filters(filters))
        return valid_transactions
    
    def _handle_initialization_error(self, method, exception: Exception) -> str:
        error_msg = f"An error occurred while ({method}): {exception}"
        log_error(error=error_msg, doc=BANK_TRANSACTION_STAGING_DOCTYPE)
        return "Error"
        
    def _start_process(self, staging_transactions, args):
        try:
            ChunkOrchestrator().process(
                self._batch_process,
                step_id=args["step_id"],
                is_enqueueable=True,
                chunk_size=int(args["chunk_size"]),
                queue=args["queue"],
                is_async=True,
                job_name="Bank Transaction Creation",
                timeout=25000,
                data_var_name="staging_transactions",
                staging_transactions=staging_transactions
            )
        except Exception as e:
            raise BankStagingException("_start_process", f"{staging_transactions} -> {e}")

    @ChunkOrchestrator.update_chunk_status
    def _batch_process(self, staging_transactions):
        status = "Processed"
        try:
            fiscal_year = get_fiscal_year()[0]['name']
            staging_process = BankStagingProcess(fiscal_year)
            staging_process.process(staging_transactions)
        except Exception as e:
            status = self._handle_initialization_error("_batch_process",e)
        return status

    @ChunkOrchestrator.update_chunk_status
    def initialize(self, args: dict) -> str:
        status = "Processed"
        try:
            self._validate() 
            self._tag_skipped() 
            self._handle_withdrawal_incident() # Need to test later 
            self._start_process(self._get_valid_transactions(), args)
        except Exception as e:
            status = self._handle_initialization_error("_batch_process",e)
        return status

class TransactionCreator(BankStagingUtils):
    """
    TransactionCreator: Handles the creation and processing of bank transactions from staging.

    Methods:
        _create_transaction_doc: Creates a bank transaction document from the staging document.
        _build_transaction_dict: Constructs a dictionary of bank transaction details from the staging document.
        _insert_transaction_doc: Inserts and submits a new bank transaction document.
        _handle_post_insert: Manages actions after a bank transaction document is created, like fiscal year updates.
    """

    def __init__(self, fiscal_year):
        self.fiscal_year = fiscal_year

    # Bank Transaction document creation and post-processing
    def _create_transaction_doc(self, staging_doc):
        reference_number = self.get_reference_number(staging_doc)  
        bt_dict = self._build_transaction_dict(staging_doc, reference_number)  
        bt_doc = self._insert_transaction_doc(bt_dict)  
        self._handle_post_insert(bt_doc, reference_number, staging_doc)

    def _build_transaction_dict(self, staging_doc, reference_number):
        return {
            "doctype": BANK_TRANSACTION_DOCTYPE,
            "date": staging_doc.date,
            "bank_account": staging_doc.bank_account,
            "deposit": staging_doc.deposit,
            "withdrawal": staging_doc.withdrawal,
            "currency": "INR",
            "description": staging_doc.description,
            "reference_number": reference_number,
            "unallocated_amount": staging_doc.deposit,
            "party_type": "Customer",
            "custom_party_group": staging_doc.payer_group,
            "custom_staging_id": staging_doc.name,
            "party": staging_doc.payer_name,
            "custom_based_on": staging_doc.based_on,
            "custom_internal_id": staging_doc.internal_id,
            "custom_file_upload": staging_doc.file_upload,
            "custom_transform": staging_doc.transform,
            "custom_index": staging_doc.index,
            "custom_yearly_due": [{'fiscal_year': self.fiscal_year, 
                                   'due_amount': 0}]
        }

    def _insert_transaction_doc(self, bt_dict):
        bt_doc = frappe.get_doc(bt_dict)
        bt_doc.insert(ignore_permissions=True)
        bt_doc.submit()
        frappe.db.commit()
        return bt_doc

    def _handle_post_insert(self, bt_doc, reference_number, staging_doc):
        file_records.create(
            is_commit=False,
            file_upload=bt_doc.custom_file_upload,
            transform=bt_doc.custom_transform,
            reference_doc=bt_doc.doctype,
            record=bt_doc.name,
            index=bt_doc.custom_index,
        )

        status = "Warning" if reference_number == "0" else "Processed"  
        remark = (
            "System Generated Reference Number" if reference_number == "0" else ""
        )  
        self._update_staging_doc(
            staging_doc.name,
            reference_number=bt_doc.name,
            staging_status=status,
            remark=remark,
            last_processed_date=today(),
            retry=0
        )


class BankStagingProcess(TransactionCreator):
    """
    BankStagingProcess: Handles the validation and processing of bank transaction staging documents.

    Attributes:
        TAG (str): A constant tag to identify credit payment transactions.
        bank_transaction_staging (frappe.qb.DocType): Represents the 'Bank Transaction Staging' DocType.
        bank_transaction (frappe.qb.DocType): Represents the 'Bank Transaction' DocType.

    Methods:
        _validate_staging: Validates the staging document, checking deposit, withdrawal, and reference number.
        _validate_deposit_withdrawal: Checks deposit and withdrawal amounts for correct transaction handling.
        _update_staging_doc: Updates the staging document with provided key-value pairs.
        _process_reference_number: Clears transactions and creates a new bank transaction document for a reference number.
        process: Iterates through transactions, validating and processing each staging document.
    """
    def __init__(self, fiscal_year):
        super().__init__(fiscal_year)

    def _validate_staging(self, staging_doc):
        deposit_amount = int(staging_doc.deposit)
        withdrawal_amount = int(staging_doc.withdrawal)

        result, error_code = self._validate_deposit_withdrawal(
            deposit_amount, withdrawal_amount
        )
        if result:
            return result, error_code

        if staging_doc.update_reference_number and staging_doc.retry == 1:
            if not self._is_reference_number_valid(staging_doc.update_reference_number):
                return "Error", "E102"
            else:
                return self._process_reference_number(staging_doc)

        return None, None

    def _validate_deposit_withdrawal(self, deposit_amount, withdrawal_amount):  
        if deposit_amount == 0 and withdrawal_amount == 0:  
            return "Error", "E101"
        elif withdrawal_amount != 0:  
            return "Skipped", None
        elif deposit_amount == 1:
            return "Error", "E104"
        return None, None

    def _update_staging_doc(self, staging_doc_name, **kwargs):
        DatabaseUtils.update_doc(BANK_TRANSACTION_STAGING_DOCTYPE, staging_doc_name, **kwargs)

    def _process_reference_number(self, staging_doc):
        if self.is_bank_trasaction_payments_present(staging_doc.reference_number):
            return "Error", "E103"

        # self.clear_transaction_and_files(staging_doc.reference_number)
        # self._create_transaction_doc(staging_doc)
        frappe.rename_doc("Bank Transaction", staging_doc.reference_number, staging_doc.update_reference_number)
        frappe.db.commit()
        return "Processed", "User Generated Reference Number"
    
    def process(self, transactions):
        for transaction in transactions:
            staging_doc = frappe.get_doc(BANK_TRANSACTION_STAGING_DOCTYPE, transaction['name'])
            try:
                staging_status, ref_code = self._validate_staging(
                    staging_doc
                ) 

                if staging_status:  
                    if staging_status in ["Error", "Skipped"]:
                        self._update_staging_doc(
                            staging_doc.name,
                            staging_status=staging_status,
                            error=ref_code,
                            remark=STAGING_ERROR_LOG.get(ref_code, None),
                            retry=0
                        )
                    elif staging_status == "Processed":
                        self._update_staging_doc(
                            staging_doc.name, 
                            staging_status=staging_status, 
                            remark=ref_code,
                            last_processed_date=today(),
                            retry=0
                        )
                    continue
                else:
                    self._create_transaction_doc(staging_doc)
            except Exception as e:
                error_code = "E100" if self.check_bt_exists(staging_doc.reference_number) else "E105"
                error_msg = f"An error occurred while (process): {e}"
                self._update_staging_doc(
                    staging_doc.name,
                    staging_status="Error",
                    error=error_code,
                    remark=STAGING_ERROR_LOG.get(error_code, None),
                    retry=0
                )
                log_error(error=error_msg, doc_name=transaction['name'], doc=BANK_TRANSACTION_STAGING_DOCTYPE)
        frappe.db.commit()

@frappe.whitelist()
def process(args: str) -> None:
    """Start the chunk creation process."""
    try:
        args: dict = cast_to_dic(args)
        ChunkOrchestrator().process(
            BankStagingProcessInitiator().initialize, 
            step_id = args["step_id"], 
            args=args
        )
    except Exception:
        log_error(error=traceback.format_exc(), doc=BANK_TRANSACTION_STAGING_DOCTYPE)

@frappe.whitelist()
def process_items(items) -> None: 
    """External API for Specific Item Processing"""
    try:
        BankStagingProcessInitiator().process_manual([items])
        fiscal_year = get_fiscal_year()[0]['name']
        staging_process = BankStagingProcess(fiscal_year)
        staging_process.process([items])
    except Exception as e:
        error_msg = f"An error occurred while (process_items): {items} -> {e}"
        log_error(error=error_msg, doc=BANK_UPDATE_DOCTYPE)
