import frappe
from agarwals.reconciliation.step.cancellator.utils.payment_entry_cancellator import PaymentEntryCancellator
from agarwals.reconciliation.step.cancellator.utils.journal_entry_cancellator import JournalEntryCancellator
from  agarwals.utils.error_handler import log_error

class PaymentDocumentCancellator:
        def cancel_payment_documents(self,bill):
            try:
                    PaymentEntryCancellator().cancel_payment_entry(bill)
                    journal_entry_doc = frappe.get_all('Journal Entry Account',
                                                            filters={'reference_name': bill, 'reference_type': 'Sales Invoice'},
                                                            pluck='parent')
                    if journal_entry_doc:
                        JournalEntryCancellator.cancel_journal_entry(bill)
            except Exception as e:
                log_error(e,'Payment Entry', bill)
