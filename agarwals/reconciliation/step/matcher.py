import frappe
from agarwals.utils.matcher_utils import update_bill_no_separate_column
from tfs.orchestration import ChunkOrchestrator
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from agarwals.utils.index_update import update_index
from agarwals.utils.matcher_query_list import get_matcher_query
from agarwals.reconciliation.step.key_mapper.claim_key_mapper import query_mapper as claim_key_queries
from agarwals.reconciliation.step.key_mapper.utr_key_mapper import query_mapper as utr_key_queries

"""
'Open' -> New Records.
'Warning' -> Validation Error.
'Fully Processed' -> Processed Records.
'Partially Processed' -> Partially Processed Records.
'Error' -> System Error.
'Unmatched' -> Unmatched Records For Other Queries.
"""

class DataIntegrityValidator:

    def __check_empty_key(self, _key_type, _doctype, _query):
        """Run Query and Check if there is any empty key present in key_type doctype."""
        query_result = frappe.db.sql(_query, as_dict=True)
        if query_result:
            raise ValueError(f'{_key_type} should not be empty in {_doctype}')

    def __check_key(self, key_type, key_queries):
        """Get corresponding queries and doctype from the key_queries."""
        for doctype, query in key_queries.items():
            self.__check_empty_key(key_type, doctype, query)

    def __check_claim_key(self):
        """Wrapper for check_key (claim_key)."""
        self.__check_key('Claim Key', claim_key_queries)

    def __check_utr_key(self):
        """Wrapper for check_key (utr_key)."""
        self.__check_key('UTR Key', utr_key_queries)

    def __is_match_logic_exist(self):
        """Check if match logic is defined in the Control Panel."""
        control_panel = frappe.get_single("Control Panel")
        match_logics = control_panel.get('match_logic','').split(",")

        if not match_logics:
            raise ValueError('Match Logic is not defined in control panel')

    def _validate(self):
        """Check all the pre validation parts"""
        self.__is_match_logic_exist()
        self.__check_utr_key()
        self.__check_claim_key()

class MatcherValidation:
    """A class to validate matcher records before processing.
        Methods:
            is_valid(): Validates the record using multiple checks.
            _validate_advice(): Validates the status of the settlement advice.
            round_off(amount): Rounds off the provided amount to 2 decimal places.
            _validate_amount(): Validates that the claim and settled amounts are correct.
            _validate_bill_status(): Checks the status of the bill.
            _validate_bank_transaction(): Validates the bank transaction details.
    """
    def __init__(self, record):
        self.record = record

    def is_valid(self):
        """Runs all validation checks on the record."""
        return (
            self._validate_advice()
            and self._validate_bill_status()
            and self._validate_bank_transaction()
            and self._validate_amount()
        )

    def _validate_advice(self):
        """Validate the settlement advice status"""
        if self.record["advice"] and self.record.status not in (
            "Open",
            "Not Processed",
        ):
            return False
        return True

    @staticmethod
    def round_off(amount):
        """Rounds off the provided amount to 2 decimal places."""
        if amount:
            return round(float(amount), 2)
        else:
            return float(0)

    def _validate_amount(self):
        """
        Validates that the claim amount is greater than 0, and that the 
        settled amount, TDS, and disallowance amounts are consistent.
        """
        claim_amount = MatcherValidation.round_off(self.record.claim_amount)
        settled_amount = MatcherValidation.round_off(self.record.settled_amount)
        tds_amount = MatcherValidation.round_off(self.record.tds_amount)
        disallowed_amount = MatcherValidation.round_off(self.record.disallowed_amount)
        tolerance = -1

        if claim_amount <= 0:
            if self.record["advice"]:
                Matcher.update_advice_status(
                    self.record["advice"], "Warning", "Claim Amount should not be 0"
                )
            return False

        elif settled_amount <= 0:
            if self.record["advice"]:
                Matcher.update_advice_status(
                    self.record["advice"], "Warning", "Settled Amount should not be 0"
                )
            return False

        elif claim_amount and (settled_amount or tds_amount or disallowed_amount):
            cumulative_amount = settled_amount + tds_amount + disallowed_amount
            difference_amount = claim_amount - cumulative_amount
            
            if difference_amount != 0:
                if difference_amount <= tolerance:
                    if self.record["advice"]:
                        Matcher.update_advice_status(
                            self.record["advice"],
                            "Warning",
                            "Claim Amount is lesser than the sum of Settled Amount, TDS Amount and Disallowance Amount."
                        )
                    return False
        return True

    def _validate_bill_status(self):
        """Checks the status of the bill to ensure it is valid for processing."""
        if frappe.get_value("Bill", self.record["bill"], "status") in [
            "CANCELLED",
            "CANCELLED AND DELETED"
        ]:
            if self.record["advice"]:
                Matcher.update_advice_status(
                    self.record["advice"], 
                    "Warning", 
                    "Cancelled Bill"
                )
            return False
        if frappe.get_value("Sales Invoice", self.record["bill"], "status") == "Paid":
            if self.record["advice"]:
                Matcher.update_advice_status(
                    self.record["advice"],
                    "Warning",
                    "Already Paid Bill"
                )
            return False
        return True

    def _validate_bank_transaction(self):
        """Validates the bank transaction details, ensuring reference numbers are valid and deposit amounts are sufficient."""
        if self.record.get("bank", ""):
            if len(self.record["bank"]) < 4:
                if self.record["advice"]:
                    Matcher.update_advice_status(
                        self.record["advice"],
                        "Warning",
                        "Reference number should be minimum of 4 digits"
                    )
                return False

            if (int(frappe.get_value("Bank Transaction", self.record["bank"], "deposit")) < 8):
                if self.record["advice"]:
                    Matcher.update_advice_status(
                        self.record["advice"],
                        "Warning",
                        "Deposit amount should be greater than 7"
                    )
                return False

            if (frappe.get_value("Bank Transaction", self.record["bank"], "status") in ["Reconciled", "Settled"]):
                if self.record["advice"]:
                    Matcher.update_advice_status(
                        self.record["advice"], "Warning", "Already Reconciled"
                    )
                return False
            
            if (frappe.get_value("Bank Transaction", self.record["bank"], "status") == "Cancelled"):
                if self.record["advice"]:
                    Matcher.update_advice_status(
                        self.record["advice"], "Warning", "Cancelled Bank Transaction"
                    )
                return False
            
        return True


class Matcher:
    """
    A class to handle the creation and processing of matcher records.
    Methods:
        add_log_error(error, doc, doc_name): Logs errors encountered during processing.
        update_payment_order(matcher_record, record): Updates payment order in matcher records.
        update_matcher_amount(matcher_record, record): Updates amounts in matcher records.
        get_matcher_name(_prefix, _suffix): Generates names for matcher records.
        update_advice_status(sa_name, status, msg): Updates the status of a settlement advice.
        create_matcher_record(matcher_records): Processes and saves matcher records.
    """

    def __init__(self, match_logics):
        self.match_logics = match_logics
        self.matcher_delete_queury = """Delete from `tabMatcher` where match_logic not in %(match_logics)s"""
        self.preprocess_update_queury = """UPDATE `tabSettlement Advice` SET status = 'Open', remark = NULL, matcher_id = NULL WHERE status IN ('Unmatched', 'Open')"""
        self.postprocess_update_query = """UPDATE `tabSettlement Advice` set status = 'Unmatched', remark = %(remark)s where status = 'Open'"""
        self.notprocessed_update_query = """UPDATE `tabSettlement Advice`SET status = %(status)s, matcher_id = %(matcher_id)s WHERE name = %(name)s"""
        self.status_update_query = """UPDATE `tabSettlement Advice` SET status = %(status)s, remark = %(remark)s WHERE name = %(name)s"""
        
    def add_log_error(self, error, doc=None, doc_name=None):
        """Logs errors encountered during processing."""
        log_error(error=error, doc=doc, doc_name=doc_name)

    def update_payment_order(self, matcher_record, record):
        """Updates the payment order in matcher records."""
        matcher_record.set("payment_order", record["payment_order"])
        return matcher_record

    def update_matcher_amount(self, matcher_record, record):
        """Updates the claim, settled, TDS, and disallowance amounts in matcher records."""
        matcher_record.set("claim_amount", record["claim_amount"])
        matcher_record.set("settled_amount", record["settled_amount"])
        matcher_record.set("tds_amount", record["tds_amount"])
        matcher_record.set("disallowance_amount", record["disallowed_amount"])
        return matcher_record

    def get_matcher_name(self, _prefix, _suffix):
        """Generates a unique name for the matcher record."""
        return f"{_prefix}-{_suffix}"

    @staticmethod
    def update_advice_status(sa_name, status, msg):
        """Update appropriate status in settlement advice"""
        advice_doc = frappe.get_doc("Settlement Advice", sa_name)
        advice_doc.status = status
        advice_doc.remark = msg
        advice_doc.save()

    def create_matcher_record(self, matcher_records, batch_size=100):
        """Processes and saves matcher records based on provided matcher logic."""
        processed_count = 0

        for record in matcher_records:
            if not MatcherValidation(record).is_valid():
                continue

            try:
                matcher_record = frappe.new_doc("Matcher")
                matcher_record.set('sales_invoice', record['bill'])
                matcher_record = self.update_matcher_amount(matcher_record, record)

                if record['advice']:
                    matcher_record.set('settlement_advice', record['advice'])

                if record['claim']:
                    matcher_record.set('claimbook', record['claim'])
                    matcher_record.set('insurance_company_name', record['insurance_name'])

                if record['logic'] in self.match_logics:
                    if record.payment_order:
                        matcher_record = self.update_payment_order(matcher_record, record)

                if record['bank']:
                    matcher_record.set('bank_transaction', record['bank'])
                    matcher_record.set('name', self.get_matcher_name(record['bill'], record['bank']))
                else:
                    if record['claim']:
                        matcher_record.set('name', self.get_matcher_name(record['bill'], record['claim']))
                    else:
                        matcher_record.set('name', self.get_matcher_name(record['bill'], record['advice']))

                matcher_record.set('match_logic', record['logic'])
                matcher_record.set('status', 'Open')
            except Exception as err:
                self.add_log_error(f'{err}: create_matcher_record', "Matcher", matcher_record.get("name", "Unknown"))

            try:
                matcher_record.save()
                
                if record["advice"]:
                    frappe.db.sql(
                        self.notprocessed_update_query,
                        values={
                            "status": "Not Processed",
                            "matcher_id": matcher_record.name,
                            "name": matcher_record.settlement_advice,
                        }
                    )
                processed_count += 1

                if processed_count % batch_size == 0:
                    frappe.db.commit()

            except Exception as err:
                if record["advice"]:
                    frappe.db.sql(
                        self.status_update_query,
                        values={
                            "status": "Error",
                            "remark": err,
                            "name": matcher_record.settlement_advice
                        }
                    )
                    
        frappe.db.commit() #safe commit

class MatcherOrchestrator(Matcher):
    """
    A class that orchestrates the processing of matcher records, handling both 
    pre-processing and post-processing tasks.
    Methods:
        preprocess_entries(): Runs pre-processing SQL queries.
        postprocess_entries(): Runs post-processing SQL queries and updates.
        get_records(): Fetches records from the database for processing.
        start_process(): The main function to trigger the processing of matcher records.
    """
    def __init__(self, match_logics):
        super().__init__(match_logics)

    def preprocess_entries(self):
        """
        Runs SQL queries to prepare the database for processing.
        """
        try:
            update_bill_no_separate_column()
            frappe.db.sql(self.matcher_delete_queury, values={"match_logics": self.match_logics})
            frappe.db.sql(self.preprocess_update_queury)
            frappe.db.commit()
        except Exception as e:
            self.add_log_error(f'{e}: preprocess_entries', 'Matcher')
            frappe.throw(f'{e}: preprocess_entries (Matcher)')

    def postprocess_entries(self):
        """Runs SQL queries for post-processing tasks like updating status for unmatched entries."""
        try:
            frappe.db.sql(self.postprocess_update_query, values={"remark": "Not able to find Bill"})
            frappe.db.commit()
        except Exception as e:
            self.add_log_error(f'{e}: postprocess_entries', 'Matcher')
            frappe.throw(f'{e}: postprocess_entries (Matcher)')

    def get_records(self, match_logic):
        """Fetches records from the database based on the control panel configuration."""
        try:
            return frappe.db.sql(get_matcher_query(match_logic), as_dict=True)
        except Exception as e:
            self.add_log_error(f'{e}: get_records', 'Matcher')
            frappe.throw(f'{e}: get_records : Matcher')

    @ChunkOrchestrator.update_chunk_status
    def start_process(self):
        """The main function to trigger the processing of matcher records in chunks."""
        status = "Processed"
        try:
            self.preprocess_entries()
            update_index()

            for match_logic in self.match_logics:
                records = self.get_records(match_logic)
                self.create_matcher_record(records)
        except Exception as e:
            status="Error"
            self.add_log_error(f'{e}: start_process', 'Matcher')

        self.postprocess_entries()
        return status

@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    step_id = args["step_id"]
    try:
        DataIntegrityValidator()._validate()
        match_logics = frappe.get_doc('Control Panel').get('match_logic','')
        if match_logics:
            match_logics = match_logics.split(',')

        matcher_orchestrator = MatcherOrchestrator(match_logics)
        ChunkOrchestrator().process(matcher_orchestrator.start_process, step_id=step_id)
    except Exception as err:
        log_error(f'{err}: process', "Matcher")
