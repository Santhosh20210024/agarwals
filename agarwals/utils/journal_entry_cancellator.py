import frappe

class JournalEntryCancellator:
    def cancel_journal_entry(self, journal_entry_doc):
        for entry in journal_entry_doc:
            journal_entry = frappe.get_doc('Journal Entry', entry)
            journal_entry.cancel()