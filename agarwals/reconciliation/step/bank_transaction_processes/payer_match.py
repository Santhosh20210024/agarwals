import frappe
import traceback
from tfs.orchestration import ChunkOrchestrator
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error,CGException
from ... import BANK_TRANSACTION_STAGING_DOCTYPE
from agarwals.reconciliation.step.bank_transaction_processes.tagger_utils import compile_patterns

class PayerMatcherException(CGException):
    def __init__(self, method_name, error):
        super().__init__(method_name, error)

class PayerMatcher:
    """
        PayerMatcher: Handles the update of payer names in bank transactions 
        based on customer priority and defined match patterns.

        This class processes bank transaction records to ensure accurate 
        payer information is recorded, prioritizing customer matches 
        as specified in the database.
    """
    
    def __init__(self) -> None:
        """
        Handles the payer name update based on customer priority and match patterns.
        """
        self.customer_fields: list[str] = ['name', 'custom_payer_match', 'customer_group']
        self.bank_transaction_staging = frappe.qb.DocType('Bank Transaction Staging')
        self.__CUSTOMER_MATCH_QUERY: str = """
                                    UPDATE `tabBank Transaction Staging` tbt SET tbt.payer_name = %(payer)s,
                                    tbt.payer_group = %(payer_group)s where search REGEXP %(customer_match_patterns)s 
                                    AND ( tbt.payer_name is NULL or tbt.payer_name = 'TPA Receipts' )
                                    """

    def _update_customer_matches(self, customers: list) -> None:
        """Customer-wise match check and update the payer name."""
        for customer in customers:
            customer_match_patterns: str = compile_patterns(customer.custom_payer_match.strip().split(","))
            if customer_match_patterns:
                frappe.db.sql(self.__CUSTOMER_MATCH_QUERY, 
                              values={'payer': customer.name,
                                      'payer_group': customer.customer_group,
                                      'customer_match_patterns': customer_match_patterns})
                frappe.db.commit()

    def _update_tpa_receipts(self) -> None:
        """Update remaining records as TPA Receipts."""
        try:
            frappe.qb.update(self.bank_transaction_staging) \
                .set(self.bank_transaction_staging.payer_name, 'TPA Receipts') \
                .set(self.bank_transaction_staging.payer_group, 'TPA/INSURANCE') \
                .where(self.bank_transaction_staging.payer_name.isnull()) \
                .run()
            frappe.db.commit()
        except Exception as e:
            raise PayerMatcherException("_update_tpa_receipts", e)

    def _get_customer_list(self, priority: str) -> list[dict[str, str, str]]:
        """Retrieve the customer list based on priority."""
        customer_list = frappe.get_all('Customer',
                                        fields=self.customer_fields,
                                        filters={'custom_payer_match': ["is", "set"],
                                                 'custom_payer_priority': ["is", priority]},
                                        order_by='custom_payer_priority asc')
        return customer_list

    def _process_matching(self) -> None:
        """Process matching for different priorities."""
        try:
            for priority in ["set", "not set"]:
                self._update_customer_matches(self._get_customer_list(priority))
        except Exception as e:
            raise PayerMatcherException("_process_matching", e)

    def start_payer_match(self) -> None:
        """Start the payer matching process and update remaining records."""
        try:
            self._process_matching()
            self._update_tpa_receipts()
        except Exception as e:
            raise PayerMatcherException("start_payer_match", e)

@ChunkOrchestrator.update_chunk_status
def initialize_payer_match() -> str:
    status: str = "Processed"
    try:
        payer_name_updater = PayerMatcher()
        payer_name_updater.start_payer_match()
    except Exception as e:
        log_error(e, BANK_TRANSACTION_STAGING_DOCTYPE)
        status = "Error"
    return status

@frappe.whitelist()
def process(args: str) -> None:
    """Start the chunk creation and update process."""
    try:
        args = cast_to_dic(args)
        ChunkOrchestrator().process(initialize_payer_match, step_id=args["step_id"])
    except Exception:
        log_error(traceback.format_exc(), BANK_TRANSACTION_STAGING_DOCTYPE)