import frappe
import traceback
from tfs.orchestration import ChunkOrchestrator
from ... import BANK_TRANSACTION_STAGING_DOCTYPE
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error, CGException
from agarwals.utils.index_update import update_index
from agarwals.reconciliation.step.bank_transaction_processes.tagger_utils import (
    TagType,
    get_tagger_query,
    compile_patterns
)

class InsuranceTaggerException(CGException):
    def __init__(self, method_name, error):
        super().__init__(method_name, error)

class InsuranceTagger:
    def __init__(self) -> None:
        """
        Initializes the InsuranceTagger class for handling and identifying credit payments based on:
            1) Insurance Pattern
            2) Settlement Advice Reference Number
            3) ClaimBook Reference Number
        
        This class is responsible for processing bank transactions and tagging them
        according to specified patterns. It manages the inclusion and exclusion of 
        transactions based on defined criteria and logs any actions taken.

        Attributes:
        INSURANCE_TAG (str): The tag used to mark credit payments.
        update_index_list (list): List of doctype names to be updated in the index.
        compiled_inclusion_patterns (str): Compiled regex patterns for inclusion checks.
        compiled_exclusion_patterns (str): Compiled regex patterns for exclusion checks.
        
        """
        self.INSURANCE_TAG: str = "Credit Payment"
        self.update_index_list: list = ['Bank Transaction Staging', 'Settlement Advice', 'ClaimBook']
        self.compiled_inclusion_patterns: str = compile_patterns(
            self._get_patterns_by_type("Inclusion")
        )
        self.compiled_exclusion_patterns: str = compile_patterns(
            self._get_patterns_by_type("Exclusion")
        )

    def update_log(self, _doc_name:str) -> None:
        """Update the deleted transaction information in error record log."""
        error_message: str = f'Bank Transaction: {_doc_name} is deleted due the changes on inclusion and exclusion patterns'
        log_error(error_message, doc=BANK_TRANSACTION_STAGING_DOCTYPE, doc_name=_doc_name, status='INFO')
    
    @DeprecationWarning
    def delete_bank_transaction(self, _doc_name:str, _doctype:str = 'Bank Transaction') ->  None:
        """Delete the bank transaction based on new exclusion patterns."""
        try:
            frappe.get_doc(_doctype, _doc_name).cancel()
            frappe.delete_doc(_doctype, _doc_name)
            self.update_log(_doc_name)
        except Exception as e:
            raise InsuranceTaggerException('delete_bank_transaction', e)

    @DeprecationWarning
    def __exclude_transactions(self) -> None:
        """Wrapper for the delete_bank_transaction method."""
        transaction_list: list = frappe.db.sql(TagType.EXCLUDE_CHECK, as_dict = 1)
        for _item in transaction_list:
            try:
                if not frappe.get_all('Bank Transaction Payments', filters={'parent': _item['bank_name']}, pluck="name"):
                    self.delete_bank_transaction('Bank Transaction', _item['bank_name'])
                    frappe.set_value(BANK_TRANSACTION_STAGING_DOCTYPE, _item['staging_name'], "staging_status", "Skipped" )
                else:
                    bts = frappe.get_doc(BANK_TRANSACTION_STAGING_DOCTYPE, _item['staging_name'] )
                    bts.staging_status = 'Error'
                    bts.error = 'E106: Insurance Tag is removed by user but the transaction is already reconciled'
                    bts.remarks = ''
                    bts.save()
            except Exception as e:
                log_error(e, BANK_TRANSACTION_STAGING_DOCTYPE)

    def _get_patterns_by_type(self, _type:str) -> list[str]:
        """Retrieves patterns from the database based on type (Inclusion/Exclusion)."""
        patterns: list = frappe.get_all(
            "Insurance Pattern", filters={"pattern_type": _type}, pluck="pattern"
        )
        return patterns

    def  __check_index_exists(self):
        for item in self.update_index_list:
            if not frappe.db.exists('Index Updation', item):
                raise ValueError(f"{item} Index does not exist in the Index Updation Doctype.")

    def __check_tag_exists(self) -> None:
        """Check the existence of appropriate tag on Tag DocType."""
        tag: list[dict] = frappe.get_all("Tag", filters={"name": self.INSURANCE_TAG})
        if not tag:
            raise ValueError("Credit Payment Tag does not exist in Tag Doctype.")
    
    def __any_empty_records(self) -> None:
        """Check if there is any empty search records in bank staging."""
        empty_search_records: list[dict] = frappe.get_all(BANK_TRANSACTION_STAGING_DOCTYPE, filters={"search": ["=", ""], "deposit": ['!=', None]})
        if empty_search_records:
            raise ValueError("One or more records have empty search field values.")
    
    def __is_inclusion_exists(self) -> None:
        """Check the existence of inclusion patterns."""
        if not self.compiled_inclusion_patterns and self.compiled_inclusion_patterns == "(?:)":
            raise ValueError("No inclusion patterns were found.")
    
    def __is_exclusion_exists(self) -> None:
        """Check the existence of exclusion patterns."""
        if not self.compiled_exclusion_patterns or self.compiled_exclusion_patterns == "(?:)":
            raise ValueError("No Exclusion patterns were found.")

    def __execute_query(self, tag_type:TagType, **kwargs:dict) -> None:
        """Executes a query based on the tag type and commits the transaction."""
        try:
            kwargs.update({"tag": self.INSURANCE_TAG})
            query: str = get_tagger_query(tag_type)
            frappe.db.sql(query, kwargs)
            frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            raise InsuranceTaggerException('__execute_query', e)
    
    def __process(self) -> None:
        """Runs multiple queries to tag transactions and handles dependent queries."""
        try:
            # Start a transaction
            self.__execute_query(TagType.INCLUSION, patterns=self.compiled_inclusion_patterns)
            self.__execute_query(TagType.EXCLUSION, patterns=self.compiled_exclusion_patterns)
            self.__execute_query(TagType.ADVICE)
            self.__execute_query(TagType.CLAIM)
            #   Delete the bank transaction if new exclusion patterns applied
            #   self.__exclude_transactions() # it leads to unnecessary deletion
        except Exception as e:
            raise InsuranceTaggerException('__process', e)

    
    def __validate_required_fields(self) -> None:
        """Validate necessary fields and throw errors if appropriate conditions are not met."""
        self.__check_index_exists()
        self.__check_tag_exists()
        self.__is_inclusion_exists()
        self.__is_exclusion_exists()
        self.__any_empty_records()
    
    def __update_index(self):
        for item in self.update_index_list:
            update_index(item)
    
    def start_tagger(self):
        self.__validate_required_fields()
        self.__update_index()
        self.__process()

@ChunkOrchestrator.update_chunk_status
def initialize_tagger() -> str:
    """Start Tagger Process and Update the chunk_doc status."""
    status = 'Processed'
    try:
        insurance_tagger_obj = InsuranceTagger()
        insurance_tagger_obj.start_tagger()
    except Exception as e:
        log_error(e, BANK_TRANSACTION_STAGING_DOCTYPE)
        status = "Error"
    return status

@frappe.whitelist()
def process(args: str) -> None:
    """Start the chunk creation and insurance tagger process"""
    try:
        args: dict = cast_to_dic(args)
        ChunkOrchestrator().process(initialize_tagger, step_id=args["step_id"])
    except Exception:
        log_error(traceback.format_exc(), BANK_TRANSACTION_STAGING_DOCTYPE)