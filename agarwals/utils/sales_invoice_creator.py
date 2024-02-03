import frappe

class SalesInvoiceCreator:
    def cancel_sales_invoice(self,cancelled_bills):
        for bill in cancelled_bills:
            try:
                sales_invoice_record = frappe.get_doc('Sales Invoice', bill)
                sales_invoice_record.cancel()
                frappe.db.commit()
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bill')
                error_log.set('reference_name', bill_no)
                error_log.set('error_message', e)
                error_log.save()


    def process(self,bill_numbers):
        for bill_number in bill_numbers:
            try:
                bill_record = frappe.get_doc('Bill', bill_number)
                sales_invoice_record = frappe.new_doc('Sales Invoice')
                sales_invoice_params = {'custom_bill_no':bill_record.bill_no,'customer':bill_record.tpa,'entity':bill_record.company,'region':bill_record.region, 'branch': bill_record.branch, 'branch_type':bill_record.branch_type, 'cost_center':bill_record.cost_center, 'items':[{'item_code': 'Claim', 'rate': bill_record.claim_amount, 'qty':1}],'set_posting_time':1, 'posting_date': bill_record.bill_date, 'due_date': bill_record.bill_date}
                for key, value in sales_invoice_params.items():
                    sales_invoice_record.set({key},{value})
                sales_invoice_record.save()
                sales_invoice_record.submit()
                if bill_record.status == 'CANCELLED':
                    sales_invoice_record.cancel()
                frappe.db.set_value('Bill', bill.bill_no, 'invoice', sales_invoice.name)
                frappe.db.commit()
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bill')
                error_log.set('reference_name', bill_no)
                error_log.set('error_message', e)
                error_log.save()

    def enqueue_jobs(self, bill_number):
        no_of_invoice_per_queue = frappe.get_single('Control Panel').no_of_sales_invoice_per_queue
        for i in range(0, len(bill_number), no_of_invoice_per_queue):
            frappe.enqueue(self.process, queue='long', is_async=True, timeout=18000, bill_numbers=bill_number[i:i + no_of_invoice_per_queue])