import frappe

class JournalUtils():
    def create_journal_entry(self, type, date):
        je = frappe.new_doc('Journal Entry')
        je.voucher_type = type
        je.posting_date = date
        return je

    def fetch_invoice_details(self, invoice):
        return frappe.get_doc('Sales Invoice', invoice)

    def add_account_entries(self, je, invoice, from_account, to_account, amount):
        je.append('accounts', {
                'account': from_account,
                'party_type': 'Customer',
                'party': invoice.customer,
                'credit_in_account_currency': amount,
                'reference_type': 'Sales Invoice',
                'reference_name': invoice.name,
                'reference_due_date': invoice.posting_date,
                'region': invoice.region,
                'entity': invoice.entity,
                'branch': invoice.branch,
                'cost_center': invoice.cost_center,
                'branch_type': invoice.branch_type
                })

        je.append('accounts', {
        'account': to_account,
        'party_type': 'Customer',
        'party': invoice.customer,
        'debit_in_account_currency': amount,
        'user_remark': to_account,
        'region': invoice.region,
        'entity': invoice.entity,
        'branch': invoice.branch,
        'cost_center': invoice.cost_center,
        'branch_type': invoice.branch_type
        })

        return je

    def save_je(self, je):
        je.save()
        je.submit()
        frappe.db.commit()

class BillAdjustmentProcess(JournalUtils):
    def __init__(self):
       super().__init__()

    def process_bill_adjust(self, bill_list):
        for bill_adjt in bill_list:
            invoice = self.fetch_invoice_details(bill_adjt.bill)
            valid_tds = False
            valid_dis = False

            try:
                if bill_adjt.tds:
                    je = self.create_journal_entry('Credit Note', bill_adjt.posting_date)
                    je.name = "".join([bill_adjt.bill,'-','TDS'])
                    je = self.add_account_entries(je, invoice, 'Debtors - A', 'TDS - A', bill_adjt.tds)
                    self.save_je(je)
                    valid_tds = True

            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bill Adjustment')
                error_log.set('reference_name', bill_adjt.bill)
                error_log.set('error_message', '' + str(e))
                error_log.save()

            try:
                if bill_adjt.disallowance:
                    je = self.create_journal_entry('Credit Note', bill_adjt.posting_date)
                    je.name = "".join([bill_adjt.bill,'-','DIS'])
                    je = self.add_account_entries(je, invoice, 'Debtors - A', 'Disallowance - A', bill_adjt.disallowance)
                    self.save_je(je)
                    valid_dis = True
            
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bill Adjustment')
                error_log.set('reference_name', bill_adjt.bill)
                error_log.set('error_message', '' + str(e))
                error_log.save()

            # Need to refactor this part
            if bill_adjt.tds and bill_adjt.disallowance:
                if valid_dis and valid_tds:
                        doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                        doc.status = 'Processed'
                        doc.save()
                elif valid_tds or valid_dis:
                        doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                        doc.status = 'Partially Processed'
                        doc.save()
                else:
                    doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                    doc.status = 'Error'
                    doc.save()

            if bill_adjt.tds:
                if valid_tds:
                    doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                    doc.status = 'Processed'
                    doc.save()
                else:
                    doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                    doc.status = 'Error'
                    doc.save()
            
            if bill_adjt.disallowance:
                if valid_dis:
                    doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                    doc.status = 'Processed'
                    doc.save()
                else:
                    doc = frappe.get_doc('Bill Adjustment', bill_adjt.bill)
                    doc.status = 'Error'
                    doc.save()

@frappe.whitelist()
def run_bill_adjust():
    n = 100
    batch_number=0
    bills = frappe.get_list('Bill Adjustment', fields = ['bill','tds','disallowance','posting_date'], filters = {'status': 'Open'})

    for _index in range(0, len(bills), n):
        batch_number = batch_number + 1
        frappe.enqueue(BillAdjustmentProcess().process_bill_adjust, queue='long', is_async=True, job_name="BillAdjustmentBatch" + str(batch_number), timeout=25000,
                       bill_list = bills[_index:_index + n])