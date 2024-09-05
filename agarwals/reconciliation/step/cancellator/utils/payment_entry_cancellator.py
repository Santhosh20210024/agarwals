import frappe

class PaymentEntryCancellator:
    def get_payment_reference_doctypes(self):
        return {'Bank Transaction Payments': 'Bank Transaction', 'Sales Invoice Reference':'Sales Invoice'}

    def cancel_record(self, record):
        record.cancel()

    def delete_record(self, record):
        record.delete()

    def get_child_records(self, doctype, parent, name):
        if parent == 'Bank Transaction':
            return frappe.get_list(doctype, filters={'parenttype': parent, 'payment_entry': name}, pluck='name')
        elif parent == 'Sales Invoice' and doctype == 'Sales Invoice Reference':
            return frappe.get_list(doctype, filters={'parenttype': parent, 'entry_name': name}, pluck='name')

    def delete_payment_references(self, payment_entry):
        payment_reference_doctype_and_parent = self.get_payment_reference_doctypes()
        for doctype, parent in payment_reference_doctype_and_parent.items():
            child_records = self.get_child_records(doctype, parent, payment_entry)
            if not child_records:
                continue
            for record in child_records:
                doc = frappe.get_doc(doctype, record)
                if doc.docstatus != 2:
                    self.cancel_record(doc)
                self.delete_record(doc)

    def cancel_payment_entry(self, bill):
        payment_entry_records = frappe.get_list('Payment Entry', filters={'custom_sales_invoice': bill},
                                                pluck='name')
        if not payment_entry_records:
            return
        for record in payment_entry_records:
            self.delete_payment_references(record)
            payment_entry_record = frappe.get_doc('Payment Entry', record)
            payment_entry_record.cancel()
            bank = frappe.get_doc('Bank Transaction', payment_entry_record.reference_no).submit()