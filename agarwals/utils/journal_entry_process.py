import frappe
from datetime import datetime

# deprecated
def check_decimal(number):
    formatted_number = str(number)
    return len(formatted_number.split(".")[1]) > 2

def create_journal_entry(invoice):
    try:
        je = frappe.new_doc('Journal Entry')
        je.voucher_type = 'Journal Entry'
        je.posting_date = datetime.now().strftime("%Y-%m-%d")

        for invoice_item in invoice:
            je.append('accounts', {
                'account': 'Debtors - A',
                'party_type': 'Customer',
                'party': invoice_item.customer,
                'credit_in_account_currency': invoice_item.outstanding_amount,
                'reference_type': 'Sales Invoice',
                'reference_name': invoice_item.name,
                'reference_due_date': invoice_item.posting_date,
                'region': invoice_item.region,
                'entity': invoice_item.entity,
                'branch': invoice_item.branch,
                'cost_center': invoice_item.cost_center,
                'branch_type': invoice_item.branch_type
            })
        
            je.append('accounts', {
                'account': 'Rounded Off - A',
                'debit_in_account_currency': invoice_item.outstanding_amount,
            })

        je.save()
        je.submit()
        frappe.db.commit()

    except Exception as e:
        frappe.msgprint("Error:" + str(e))
        
def bulk_process():
    invoice = frappe.qb.DocType('Sales Invoice')
    invoice_query = (
                        frappe.qb.from_(invoice)
                            .select(invoice.name, invoice.customer, invoice.posting_date, invoice.outstanding_amount, invoice.region, invoice.entity, invoice.branch, invoice.cost_center, invoice.branch_type)
                            .where((invoice.outstanding_amount <= 9.9))
                            .where((invoice.status == 'Partly Paid'))
                    )
    
    oustanding_sales = frappe.db.sql(invoice_query, as_dict = True)
    create_journal_entry(oustanding_sales)


@frappe.whitelist()
def run():
    bulk_process()