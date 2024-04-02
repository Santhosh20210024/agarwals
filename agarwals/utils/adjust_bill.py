import frappe
from datetime import datetime

def create_journal_entry(type):
    je = frappe.new_doc('Journal Entry')
    je.voucher_type = type
    je.posting_date = datetime.now().strftime("%Y-%m-%d")
    return je

def fetch_invoice_details(invoice):
    return frappe.get_doc('Sales Invoice', invoice)

def add_account_entries(je, invoice, from_account, to_account, amount):
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

def save_je(je):
    je.save()
    je.submit()
    frappe.db.commit()

def process_bill_adjust():
    for bill_adjt in frappe.get_list('Bill Adjustments', fields = ['bill','tds','disallowance'], filters = {'status': 'Open'}):
        invoice = fetch_invoice_details(bill_adjt.bill)
        valid_tds = False
        valid_dis = False

        try:
            if bill_adjt.tds:
                je = create_journal_entry('Credit Note')
                je.name = "".join([bill_adjt.bill,'-','TDS'])
                je = add_account_entries(je, invoice, 'Debtors - A', 'TDS - A', bill_adjt.tds)
                save_je(je)
                valid_tds = True

        except Exception as e:
            error_log = frappe.new_doc('Error Record Log')
            error_log.set('doctype_name', 'Bill Adjustments')
            error_log.set('reference_name', bill_adjt.bill)
            error_log.set('error_message', '' + str(e))
            error_log.save()

        try:
            if bill_adjt.disallowance:
                je = create_journal_entry('Credit Note')
                je.name = "".join([bill_adjt.bill,'-','DIS'])
                je = add_account_entries(je, invoice, 'Debtors - A', 'Disallowance - A', bill_adjt.disallowance)
                save_je(je)
                valid_dis = True
        
        except Exception as e:
            error_log = frappe.new_doc('Error Record Log')
            error_log.set('doctype_name', 'Bill Adjustments')
            error_log.set('reference_name', bill_adjt.bill)
            error_log.set('error_message', '' + str(e))
            error_log.save()

        # Need to refactor this part
        if bill_adjt.tds and bill_adjt.disallowance:
            if valid_dis and valid_tds:
                    doc = frappe.get_doc('Bill Adjustments', bill_adjt.bill)
                    doc.status = 'Processed'
                    doc.save()
            elif valid_tds or valid_dis:
                    doc = frappe.get_doc('Bill Adjustments', bill_adjt.bill)
                    doc.status = 'Partially Processed'
                    doc.save()
            else:
                doc = frappe.get_doc('Bill Adjustments', bill_adjt.bill)
                doc.status = 'Error'
                doc.save()

        if bill_adjt.tds:
            if valid_tds:
                doc = frappe.get_doc('Bill Adjustments', bill_adjt.bill)
                doc.status = 'Processed'
                doc.save()
            else:
                doc = frappe.get_doc('Bill Adjustments', bill_adjt.bill)
                doc.status = 'Error'
                doc.save()
        
        if bill_adjt.disallowance:
            if valid_dis:
                doc = frappe.get_doc('Bill Adjustments', bill_adjt.bill)
                doc.status = 'Processed'
                doc.save()
            else:
                doc = frappe.get_doc('Bill Adjustments', bill_adjt.bill)
                doc.status = 'Error'
                doc.save()

@frappe.whitelist()
def run_bill_adjust():
    process_bill_adjust()