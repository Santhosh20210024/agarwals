import frappe


@frappe.whitelist()
def create_sales_background_job(n):
    cancelled_bills = frappe.get_list('Bill',filters={'status':'CANCELLED','invoice_status':'RAISED'},pluck = 'name')
    for bill in cancelled_bills:
        cancel_sales_invoice(bill)
    bills = frappe.db.get_list('Bill',filters = {'invoice':''},fields='*')
    n = int(n)
    
    for i in range(0, len(bills), n):
        frappe.enqueue(create_sales_invoice, queue='long', is_async=True, timeout=18000, bills=bills[i:i + n])

def cancel_sales_invoice(bill_no):
    sales_invoice = frappe.get_doc('Sales Invoice', bill_no)
    sales_invoice.cancel()
    frappe.db.set_value('Bill', bill_no, 'invoice_status', "CANCELLED")
    frappe.db.commit()

def create_sales_invoice(bills):
    try:
        for bill in bills:
            try:
                sales_invoice_existing = True if len(
                    frappe.get_list("Sales Invoice", filters={'name': bill.bill_no})) != 0 else False
                if not sales_invoice_existing:
                    sales_invoice = frappe.new_doc('Sales Invoice')
                    sales_invoice_item = [{'item_code': 'Claim', 'rate': bill.claim_amount, 'qty': 1}]
                    sales_invoice.set('bill_no', bill.bill_no)
                    sales_invoice.set('customer', bill.tpa)
                    sales_invoice.set('entity', bill.company)
                    sales_invoice.set('region', bill.region)
                    sales_invoice.set('branch',bill.branch)
                    sales_invoice.set('cost_center', bill.cost_center)
                    sales_invoice.set('items', sales_invoice_item)
                    sales_invoice.set('set_posting_time',1)
                    sales_invoice.set('posting_date', bill.bill_date)
                    sales_invoice.set('due_date', bill.bill_date)
                    sales_invoice.save()
                    sales_invoice.submit()
                    if bill.status == "CANCELLED":
                        sales_invoice.cancel()
                    frappe.db.set_value('Bill',bill.bill_no,{'invoice':sales_invoice.name, 'invoice_status':bill.status})
                    frappe.db.commit()
                    print('Sales Invoice Created')
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Sales Invoice')
                error_log.set('reference_name',bill.bill_no)
                error_log.set('error_message', e)
                error_log.save()

        return 'Success'

    except Exception as e:
        return e


