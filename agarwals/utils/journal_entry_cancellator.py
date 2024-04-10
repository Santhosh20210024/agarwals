import frappe

class JournalEntryCancellator:

    def get_journal_entry(self, bill):
         return frappe.get_list('Journal Entry Account', filters={'reference_name': bill, 'reference_type':'Sales Invoice'}, pluck = 'parent')
    def cancel_journal_entry(self, bill):
        journal_entries = self.get_jounal_entries(bill)
        if not journal_entries:
            return
        for entry in journal_entries:
            journal_entry = frappe.get_doc('Journal Entry', entry)
            journal_entry.cancel()