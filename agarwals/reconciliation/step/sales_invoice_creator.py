import frappe
from agarwals.agarwals.doctype import file_records
from agarwals.reconciliation.step.cancellator.cancellator import PaymentDocumentCancellator
from agarwals.reconciliation.step.cancellator.utils.matcher_cancellator import MatcherCancellator
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from agarwals.utils.fiscal_year_update import update_fiscal_year
from datetime import date
from erpnext.accounts.doctype.journal_entry.journal_entry import make_reverse_journal_entry

class SalesInvoiceCancellator:
    def get_bill_period(self, date):
        bill_period = frappe.get_list("Accounting Period", filters={'start_date':['<=',date],'end_date':['>=',date]})
        if not bill_period:
            return "Current Year"
        return "Previous Year"

    def get_payment_entry_documents(self, bill):
        return frappe.get_list("Payment Entry", filters={'custom_sales_invoice':bill,'status':['not in',('Draft','Cancelled')]}, fields=['name','custom_sales_invoice','paid_amount','custom_tds_amount','custom_disallowed_amount','custom_round_off','paid_to','party','reference_no','reference_date'])

    def add_account_entry(self, je, account, entry_type, amount, reference_type = None, reference_name = None, si = None):
        entry = {}
        entry['account'] =  account

        if entry_type == "credit":
            entry['credit_in_account_currency'] = amount
        else:
            entry['debit_in_account_currency'] = amount

        if si:
            entry['region'] = si.region
            entry['entity'] = si.entity
            entry['branch'] = si.branch
            entry['cost_center'] = si.cost_center
            entry['branch_type'] = si.branch_type
            entry['party_type'] = "Customer"
            entry['party'] = si.customer

        entry['reference_type'] = reference_type
        entry['reference_name'] = reference_name

        je.append('accounts', entry)
        return je



    def make_reversal_entry_for_pe(self, payment_entry_documents):
        for payment_entry in payment_entry_documents:
            journal_entry = frappe.new_doc("Journal Entry")
            journal_entry.name = payment_entry['name'] + " - Reverse"
            journal_entry.voucher_type = "Debit Note"
            journal_entry.posting_date = date.today()
            sales_invoice = frappe.get_doc("Sales Invoice", payment_entry['custom_sales_invoice'])
            journal_entry.custom_sales_invoice = payment_entry['custom_sales_invoice']
            journal_entry.custom_entity = sales_invoice.entity
            journal_entry.custom_region = sales_invoice.region
            journal_entry.custom_branch = sales_invoice.branch
            journal_entry.custom_party = sales_invoice.customer
            journal_entry.custom_party_group = sales_invoice.customer_group
            journal_entry.custom_branch_type = sales_invoice.branch_type
            journal_entry.custom_bill_date = sales_invoice.posting_date
            journal_entry.cheque_no = payment_entry['reference_no']
            journal_entry.cheque_date = payment_entry['reference_date']
            if payment_entry['paid_amount'] != 0:
                journal_entry = self.add_account_entry(je = journal_entry, account = payment_entry['paid_to'], entry_type = 'credit', amount = payment_entry['paid_amount'])
            if payment_entry['custom_tds_amount'] != 0:
                journal_entry = self.add_account_entry(je=journal_entry, si=sales_invoice,
                                                       account="TDS - A", entry_type='credit',
                                                       amount=payment_entry['custom_tds_amount'])
            if payment_entry['custom_disallowed_amount'] != 0:
                journal_entry = self.add_account_entry(je=journal_entry, si=sales_invoice,
                                                       account="Disallowance - A", entry_type='credit',
                                                       amount=payment_entry['custom_disallowed_amount'])
            if payment_entry['custom_round_off'] > 0:
                journal_entry = self.add_account_entry(je=journal_entry, si=sales_invoice,
                                                       account="Rounded Off - A", entry_type='credit',
                                                       amount=payment_entry['custom_round_off'])

            journal_entry = self.add_account_entry(je=journal_entry, si=sales_invoice,
                                                   account="Debtors - A", entry_type='debit',
                                                   amount=payment_entry['paid_amount'] + payment_entry['custom_tds_amount'] + payment_entry['custom_disallowed_amount'] + payment_entry['custom_round_off'])

            journal_entry.save()
            journal_entry.submit()
            bank_transaction = frappe.get_doc("Bank Transaction", payment_entry['reference_no'])
            bank_transaction.append('payment_entries',
                           {'payment_document': "Journal Entry"
                               , 'payment_entry': journal_entry.name
                               , 'allocated_amount': -payment_entry['paid_amount']
                               , 'custom_posting_date':journal_entry.posting_date
                               , 'custom_bill_date': sales_invoice.posting_date
                               , 'custom_bill_region': sales_invoice.region
                               , 'custom_bill_branch': sales_invoice.branch
                               , 'custom_bill_branch_type': sales_invoice.branch_type
                               , 'custom_bill_entity': sales_invoice.entity})
            bank_transaction.submit()
            frappe.db.commit()

    def get_journal_entry_documents(self, bill):
        return frappe.get_list("Journal Entry",
                               filters={'custom_sales_invoice': bill, 'docstatus': 1},pluck = 'name')

    def make_reversal_entry_for_je(self,journal_entries):
        for jounal_entry in journal_entries:
            reverse_entry = make_reverse_journal_entry(jounal_entry)
            reverse_entry.name = jounal_entry + " - Reverse"
            reverse_entry.voucher_type = "Debit Note"
            reverse_entry.posting_date = date.today()
            reverse_entry.save()
            reverse_entry.submit()
            frappe.db.commit()

    def make_cancel_je(self, bill):
        sales_invoice = frappe.get_doc("Sales Invoice", bill)
        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.name = sales_invoice.name + " - Cancel"
        journal_entry.voucher_type = "Credit Note"
        journal_entry.posting_date = date.today()
        journal_entry.custom_sales_invoice = sales_invoice.name
        journal_entry.custom_entity = sales_invoice.entity
        journal_entry.custom_region = sales_invoice.region
        journal_entry.custom_branch = sales_invoice.branch
        journal_entry.custom_party = sales_invoice.customer
        journal_entry.custom_party_group = sales_invoice.customer_group
        journal_entry.custom_branch_type = sales_invoice.branch_type
        journal_entry.custom_bill_date = sales_invoice.posting_date
        journal_entry = self.add_account_entry(je=journal_entry, si=sales_invoice,
                                               account="Debtors - A", entry_type='credit',
                                               amount=sales_invoice.outstanding_amount, reference_type="Sales Invoice", reference_name=sales_invoice.name)
        journal_entry = self.add_account_entry(je=journal_entry, si=sales_invoice,
                                               account="Sales - A", entry_type='debit',
                                               amount=sales_invoice.outstanding_amount)
        journal_entry.save()
        journal_entry.submit()
        frappe.db.commit()


    def cancel_previous_period_bill(self, bill):
        journal_entry_documents = self.get_journal_entry_documents(bill)
        if journal_entry_documents:
            self.make_reversal_entry_for_je(journal_entry_documents)
        payment_entry_documents = self.get_payment_entry_documents(bill)
        if payment_entry_documents:
            self.make_reversal_entry_for_pe(payment_entry_documents)
        self.make_cancel_je(bill)

    @ChunkOrchestrator.update_chunk_status
    def cancel_sales_invoice(self, cancelled_bills):
        status = "Processed"
        for bill in cancelled_bills:
            try:
                bill_record = frappe.get_doc('Bill', bill)
                bill_period = self.get_bill_period(bill_record.bill_date)
                if bill_period != "Current Year":
                    self.cancel_previous_period_bill(bill)
                    frappe.db.set_value('Bill', bill, {'invoice_status': 'CANCELLED'})
                    frappe.db.set_value('Sales Invoice', bill, {'status': 'Cancelled','docstatus':2, 'outstanding_amount':0})
                    frappe.db.commit()
                    continue
                sales_invoice_record = frappe.get_doc('Sales Invoice', bill)
                sales_invoice_record.custom_file_upload = bill_record.file_upload
                sales_invoice_record.custom_transform = bill_record.transform
                sales_invoice_record.custom_index = bill_record.index
                sales_invoice_record.save(ignore_permissions=True)
                PaymentDocumentCancellator().cancel_payment_documents(bill)
                MatcherCancellator().delete_matcher(sales_invoice_record)
                sales_invoice_record.reload()
                sales_invoice_record.cancel()

                frappe.db.set_value('Bill', bill, {'invoice_status': 'CANCELLED'})
                frappe.db.set_value('Sales Invoice', bill, {'outstanding_amount': 0})
                frappe.db.commit()
                file_records.create(file_upload=sales_invoice_record.custom_file_upload,
                                    transform=sales_invoice_record.custom_transform,
                                    reference_doc=sales_invoice_record.doctype,
                                    record=bill, index=sales_invoice_record.custom_index)
            except Exception as e:
                status = "Error"
                log_error(error=e, doc="Bill", doc_name=bill)
        return status

class SalesInvoiceCreator:
    @ChunkOrchestrator.update_chunk_status
    def process(self, bill_numbers, chunk_doc):
        status = "Processed"
        for bill_number in bill_numbers:
            try:
                bill_record = frappe.get_doc('Bill', bill_number)
                bill_record.set("region", frappe.get_doc('Branch', bill_record.branch).custom_region)
                bill_record.set("customer", frappe.get_doc('Payer Alias', bill_record.payer).payer_final_name)
                bill_record.set("branch_type", frappe.get_doc('Branch', bill_record.branch).custom_branch_type)
                bill_record.save()
                skip_invoice_customer_list = self.get_skip_invoice_customer()
                if bill_record.customer in skip_invoice_customer_list:
                    bill_record.set("status","CANCELLED AND DELETED")
                    bill_record.save()
                    frappe.db.commit()
                    continue
                sales_invoice_record = frappe.new_doc('Sales Invoice')
                sales_invoice_params = {'custom_bill_no': bill_record.bill_no, 'custom_mrn': bill_record.mrn,
                                        'custom_patient_name': bill_record.patient_name,
                                        'custom_ma_claim_id': bill_record.ma_claim_id,
                                        'custom_claim_id': bill_record.claim_id, 'customer': bill_record.customer,
                                        'entity': bill_record.entity, 'region': bill_record.region,
                                        'branch': bill_record.branch, 'branch_type': bill_record.branch_type,
                                        'cost_center': bill_record.cost_center,
                                        'custom_patient_age' : bill_record.patient_age,
                                        'items': [
                                            {'item_code': 'Claim', 'rate': bill_record.claim_amount, 'qty': 1}],
                                        'set_posting_time': 1, 'posting_date': bill_record.bill_date,
                                        'due_date': bill_record.bill_date,
                                        'custom_file_upload': bill_record.file_upload,
                                        'custom_transform': bill_record.transform,
                                        'custom_index': bill_record.index}
                for key, value in sales_invoice_params.items():
                    sales_invoice_record.set(key, value)
                sales_invoice_record.save()
                sales_invoice_record.submit()
                if bill_record.status == 'CANCELLED':
                    sales_invoice_record.cancel()
                frappe.db.set_value('Bill', bill_number,
                                    {'invoice': sales_invoice_record.name, 'invoice_status': bill_record.status})
                frappe.db.commit()
                if sales_invoice_record.status != 'Cancelled':
                    update_fiscal_year(sales_invoice_record, 'Sales Invoice')

                file_records.create(file_upload=sales_invoice_record.custom_file_upload,
                                    transform=sales_invoice_record.custom_transform,
                                    reference_doc=sales_invoice_record.doctype,
                                    record=bill_number, index=sales_invoice_record.custom_index)
            except Exception as e:
                status = "Error"
                log_error(error= 'Unable to Create Sales Invoice: ' + str(e), doc="Bill", doc_name=bill_number)
            chunk.update_status(chunk_doc, "Error")
        return status

    def enqueue_jobs(self, bill_number, args):
        no_of_invoice_per_queue = int(args["chunk_size"])
        for i in range(0, len(bill_number), no_of_invoice_per_queue):
            chunk_doc = chunk.create_chunk(args["step_id"])
            frappe.enqueue(self.process, queue=args["queue"], is_async=True, timeout=18000,
                           bill_numbers=bill_number[i:i + no_of_invoice_per_queue], chunk_doc=chunk_doc)
        
    def get_skip_invoice_customer(self):
        return frappe.get_all('Customer',filters = {'custom_skip_invoice_creation':1},pluck = 'name')

@ChunkOrchestrator.update_chunk_status
def create_and_cancel_sales_invoices(args: dict, new_bills: list, cancelled_bills: list) -> str:
    try:
        ChunkOrchestrator().process(SalesInvoiceCancellator().cancel_sales_invoice, step_id=args["step_id"],
                                    cancelled_bills=cancelled_bills)
        ChunkOrchestrator().process(SalesInvoiceCreator().process, step_id=args["step_id"], is_enqueueable=True,
                                    chunk_size=args["chunk_size"], data_var_name="bill_numbers", queue=args["queue"],
                                    is_async=True, timeout=18000, bill_numbers=new_bills)
        return "Processed"
    except Exception as e:
        log_error(error=e, doc="Bill")
        return "Error"

@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    cancelled_bills = frappe.get_list('Bill', filters={'status': 'CANCELLED', 'invoice_status': 'RAISED'},
                                      pluck='name')
    new_bills = frappe.get_list('Bill', filters={'invoice': '', 'status': ['!=', 'CANCELLED AND DELETED']},
                                pluck='name')
    ChunkOrchestrator().process(create_and_cancel_sales_invoices, step_id=args["step_id"], args=args,
                                new_bills=new_bills,
                                cancelled_bills=cancelled_bills)