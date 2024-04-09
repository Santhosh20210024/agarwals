import frappe


class SalesInvoiceCreator:
    def get_payment_reference_doctypes(self):
        return {'Bank Transaction Payments':'Bank Transaction'}

    def cancel_record(self,record):
        record.cancel()
    def delete_record(self,record):
        record.delete()

    def get_child_records(self, doctype, parent):
        return frappe.get_list(doctype,filters = {'parenttype':parent, 'payment_entry':name},pluck = 'name')

    def delete_payment_references(self, payment_entry):
        payment_reference_doctype_and_parent = self.get_payment_reference_doctypes()
        for doctype,parent in payment_reference_doctype_and_parent.items():
            child_records = self.get_child_records(doctype,parent)
            if not child_records:
                continue
            for record in child_records:
                doc = frappe.get_doc(doctype,record)
                self.cancel_record(doc)
                self.delete_record(doc)

    def cancel_payment_entry(self, bill):
        payment_entry_records = frappe.get_list('Payment Entry', filters={'custom_sales_invoice':bill}, pluck = 'name')
        if not payment_entry_records:
            return
        for record in payment_entry_records:
            self.delete_payment_references(record)
            payment_entry_record = frappe.get_doc('Payment Entry', record)
            payment_entry_record.cancel()

    def cancel_sales_invoice(self, cancelled_bills):
        for bill in cancelled_bills:
            try:
                sales_invoice_record = frappe.get_doc('Sales Invoice', bill)
                sales_invoice_record.cancel()
                self.cancel_payment_entry(bill)
                frappe.db.set_value('Bill', bill, {'invoice_status': 'CANCELLED'})
                frappe.db.commit()
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bill')
                error_log.set('reference_name', bill)
                error_log.set('error_message', e)
                error_log.save()

    def process(self, bill_numbers):
        for bill_number in bill_numbers:
            try:
                bill_record = frappe.get_doc('Bill', bill_number)
                bill_record.set("region", frappe.get_doc('Branch', bill_record.branch).custom_region)
                bill_record.set("customer", frappe.get_doc('Payer Alias', bill_record.payer).payer_final_name)
                bill_record.set("branch_type", frappe.get_doc('Branch', bill_record.branch).custom_branch_type)
                bill_record.save()
                sales_invoice_record = frappe.new_doc('Sales Invoice')
                sales_invoice_params = {'custom_bill_no': bill_record.bill_no, 'custom_mrn': bill_record.mrn,
                                        'custom_claim_id': bill_record.claim_id, 'customer': bill_record.customer,
                                        'entity': bill_record.entity, 'region': bill_record.region,
                                        'branch': bill_record.branch, 'branch_type': bill_record.branch_type,
                                        'cost_center': bill_record.cost_center,
                                        'items': [{'item_code': 'Claim', 'rate': bill_record.claim_amount, 'qty': 1}],
                                        'set_posting_time': 1, 'posting_date': bill_record.bill_date,
                                        'due_date': bill_record.bill_date}
                for key, value in sales_invoice_params.items():
                    sales_invoice_record.set(key, value)
                sales_invoice_record.save()
                sales_invoice_record.submit()
                if bill_record.status == 'CANCELLED':
                    sales_invoice_record.cancel()
                frappe.db.set_value('Bill', bill_number, {'invoice': sales_invoice_record.name, 'invoice_status': bill_record.status})
                frappe.db.commit()
            except Exception as e:
                error_log = frappe.new_doc('Error Record Log')
                error_log.set('doctype_name', 'Bill')
                error_log.set('reference_name', bill_number)
                error_log.set('error_message', 'Unable to Create Sales Invoice: ' + str(e))
                error_log.save()

    def enqueue_jobs(self, bill_number):
        no_of_invoice_per_queue = int(frappe.get_single('Control Panel').payment_matching_chunk_size)
        for i in range(0, len(bill_number), no_of_invoice_per_queue):
            frappe.enqueue(self.process, queue='long', is_async=True, timeout=18000,
                           bill_numbers=bill_number[i:i + no_of_invoice_per_queue])


@frappe.whitelist()
def create_sales_invoice():
    try:
        cancelled_bills = frappe.get_list('Bill', filters={'status': 'CANCELLED', 'invoice_status': 'RAISED'},
                                          pluck='name')
        if cancelled_bills:
            SalesInvoiceCreator().cancel_sales_invoice(cancelled_bills)
        new_bills = frappe.get_list('Bill', filters={'invoice': ''},pluck = 'name')
        SalesInvoiceCreator().enqueue_jobs(new_bills)
    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('error_message', e)
        error_log.save()
