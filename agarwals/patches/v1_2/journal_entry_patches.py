import frappe
from agarwals.utils.error_handler import log_error
class JournalEntryPatches:
    def change_naming_series(self):
        custom_journal_entry_records =[{
            'property' : 'naming_rule',
            'property_type' :'Data',
            'value' : 'Set by user'},
            {'property' : 'autoname',
            'property_type' :'Data',
            'value' : 'prompt'}]
    
        for record in custom_journal_entry_records :
            try:
                journal_entry_record =frappe.new_doc('Property Setter')
                journal_entry_record.update({
                    'doctype_or_field':'DocType',
                    'doc_type':'Journal Entry',
                    'property' : record.get('property'),
                    'property_type' : record.get('property_type'),
                    'value' : record.get('value')
                })
                journal_entry_record.save()
            except Exception as e:
                log_error(e, "Journal Entry")
                
        frappe.db.commit()

    def process(self):
        self.change_naming_series()


def execute():
    journal_entry_instance = JournalEntryPatches()
    journal_entry_instance.change_naming_series()