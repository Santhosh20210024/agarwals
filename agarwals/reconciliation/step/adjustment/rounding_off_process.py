import frappe
from agarwals.utils.error_handler import log_error
from agarwals.utils.accounting_utils import update_posting_date
from agarwals.reconciliation.step.adjustment.journal_entry_utils import (
    JournalEntryUtils,
)
from agarwals.utils.accounting_utils import get_abbr


class RoundOffProcess(JournalEntryUtils):

    def __init__(self, type):
        super().__init__(type)
        self.type = type
        self.ENTRY_TYPE = "RND"
        self.JOURNAL_TYPE = "Credit Note"
        self.DEBTORS_ACCOUNT = "Debtors - " + get_abbr()
        self.ROUNDED_ACCOUNT = "Rounded Off - " + get_abbr()

    def _add_custom_fields(self, je, invoice):
        je.custom_sales_invoice = invoice.name
        je.custom_entity = invoice.entity
        je.custom_branch = invoice.branch
        je.custom_region = invoice.region
        je.custom_branch_type = invoice.branch_type
        je.custom_bill_date = invoice.posting_date
        je.custom_party_group = invoice.customer_group
        je.custom_party = invoice.customer
        return je

    def get_company_account(self, bank_account):
        bank_account = frappe.get_doc("Bank Account", bank_account)
        return bank_account.account

    def get_round_off_details(self, round_off_item):
        doc = self.fetch_doc_details(self.type, round_off_item)
        if self.type == "Sales Invoice":
            return doc, doc.posting_date
        elif self.type == "Bank Transaction":
            return doc, doc.date
        return None, None

    def update_transaction_entry(self, transaction_name, je):
        try:
            bt_doc = frappe.get_doc("Bank Transaction", transaction_name)
            bt_doc.append(
                "payment_entries",
                {
                    "payment_document": "Journal Entry",
                    "payment_entry": je.name,
                    "allocated_amount": je.total_credit,
                    "custom_posting_date": je.posting_date,
                    "custom_creation_date": je.creation,
                },
            )
            bt_doc.submit()
            frappe.db.commit()
        except Exception as e:
            log_error(
                f"Error updating transaction entry: {e}",
                doc_name="RoundOffProcess.update_transaction_entry",
            )

    def process_round_off(self, round_off_items):
        for round_off_item in round_off_items:
            try:

                round_off_doc, date = self.get_round_off_details(round_off_item)
                if not round_off_doc or not date:
                    continue

                posting_date = update_posting_date(date)
                from_account = (
                    self.DEBTORS_ACCOUNT
                    if self.type == "Sales Invoice"
                    else self.get_company_account(round_off_doc.bank_account)
                )
                amount = (
                    round_off_doc.outstanding_amount
                    if self.type == "Sales Invoice"
                    else round_off_doc.unallocated_amount
                )

                je = self.create_journal_entry(self.JOURNAL_TYPE, posting_date)
                je = self.set_je_name(round_off_doc.name, "-", self.ENTRY_TYPE, je=je)
                je = self.add_account_entries(
                    je, round_off_doc, from_account, self.ROUNDED_ACCOUNT, amount
                )

                if self.type == "Sales Invoice":
                    je = self._add_custom_fields(je, round_off_doc)
                self.save_je(je)

                if self.type == "Bank Transaction":
                    self.update_transaction_entry(round_off_doc.name, je)
            except Exception as e:
                error_message = f"Error while processing {self.ENTRY_TYPE} entry in {self.type}: {e}"
                log_error(error_message, doc_name=round_off_item)


class RoundOffOrchestrator:
    def start_process(self, type, round_off_items, chunk_size=100):
        if not round_off_items:
            return

        batch_no = 0
        for round_off_chunk in self._chunk_list(round_off_items, chunk_size):
            batch_no += 1
            self._enqueue_round_off(type, round_off_chunk, batch_no)

    def _chunk_list(self, iterable, n):
        """Yield successive n-sized chunks from the iterable."""
        for i in range(0, len(iterable), n):
            yield iterable[i : i + n]

    def _enqueue_round_off(self, type, round_off_chunk, batch_no):
        try:
            frappe.enqueue(
                RoundOffProcess(type).process_round_off,
                queue="long",
                is_async=True,
                job_name=f"RoundOff_{type}_Batch{batch_no}",
                timeout=25000,
                round_off_items=round_off_chunk,
            )
        except Exception as e:
            log_error(
                f"Error enqueuing round off process for batch {batch_no}: {e}",
                doc_name="RoundOffOrchestrator._enqueue_round_off",
            )


@frappe.whitelist()
def get_invoices():
    invoice_qb = frappe.qb.DocType("Sales Invoice")
    invoice_query = (
        frappe.qb.from_(invoice_qb)
        .select(
            invoice_qb.name,
            invoice_qb.customer,
            invoice_qb.posting_date,
            invoice_qb.outstanding_amount,
            invoice_qb.region,
            invoice_qb.entity,
            invoice_qb.branch,
            invoice_qb.cost_center,
            invoice_qb.branch_type,
        )
        .where((invoice_qb.outstanding_amount <= 9.9))
        .where((invoice_qb.status == "Partly Paid") | (invoice_qb.status == "Unpaid"))
    )
    return frappe.db.sql(invoice_query, as_dict=True)


@frappe.whitelist()
def get_transactions():
    bank_qb = frappe.qb.DocType("Bank Transaction")
    bank_query = (
        frappe.qb.from_(bank_qb)
        .select(bank_qb.name, bank_qb.date, bank_qb.unallocated_amount)
        .where((bank_qb.unallocated_amount <= 9.9))
        .where((bank_qb.status == "Unreconciled"))
    )
    return frappe.db.sql(bank_query, as_dict=True)


@frappe.whitelist()
def process(_type):
    if _type == "Bank Transaction":
        bank_transactions = get_transactions()
        RoundOffOrchestrator().start_process(_type, bank_transactions)

    elif _type == "Sales Invoice":
        invoices = get_invoices()
        RoundOffOrchestrator().start_process(_type, invoices)
