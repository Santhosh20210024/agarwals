import frappe
from agarwals.reconciliation.step.adjust_bill import JournalUtils
from agarwals.utils.error_handler import log_error as error_handler


class RoundOffCreation(JournalUtils):

    def __init__(self):
        super().__init__()
        
    def process_round_off(self, rnd_outstanding_bills):
        for bill in rnd_outstanding_bills:
            invoice_ = self.fetch_invoice_details(bill)
            try:
                je = self.create_journal_entry('Credit Note', invoice_.posting_date)
                je.name = "".join([invoice_.name,'-','RND'])
                je = self.add_account_entries(je, invoice_, 'Debtors - A', 'Rounded Off - A', invoice_.outstanding_amount)
                self.save_je(je)

            except Exception as e:
                error_handler(error=str(e), doc='Journal Entry', doc_name=invoice_.name)


@frappe.whitelist()
def run(_chunk_size):
    chunk_size = int(_chunk_size)
    rq_number = 0
    invoice = frappe.qb.DocType('Sales Invoice')

    invoice_query = (
            frappe.qb.from_(invoice)
                .select(invoice.name, invoice.customer, invoice.posting_date, invoice.outstanding_amount, invoice.region, invoice.entity, invoice.branch, invoice.cost_center, invoice.branch_type)
                .where((invoice.outstanding_amount <= 9.9))
                .where((invoice.status == 'Partly Paid'))
        )
    rnd_outstanding_bills = frappe.db.sql(invoice_query, as_dict = True) 

    for _index in range(0, len(rnd_outstanding_bills), chunk_size):
        rq_number = rq_number + 1
        frappe.enqueue(RoundOffCreation().process_round_off, queue='long', is_async=True, job_name="RoundOffBatch" + str(rq_number), timeout=25000,
                    rnd_outstanding_bills = rnd_outstanding_bills[_index:_index + chunk_size])
