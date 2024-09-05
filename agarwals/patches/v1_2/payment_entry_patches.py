import frappe
from agarwals.utils.error_handler import log_error
class PaymentEntryPatches:
    def change_naming_series(self):
        custom_payment_entry_records =[{
                'property' : 'naming_rule',
                'property_type' :'Data',
                'value' : 'Set by user'},
                {'property' : 'autoname',
                'property_type' :'Data',
                'value' : 'prompt'}]
        for record in custom_payment_entry_records :
            try :
                payment_entry_record =frappe.new_doc('Property Setter')
                payment_entry_record.update({
                    'doctype_or_field':'DocType',
                    'doc_type':'Journal Entry',
                    'property' : record.get('property'),
                    'property_type' : record.get('property_type'),
                    'value' : record.get('value')
                })
                payment_entry_record.save()
            except Exception as e:
                log_error(e, "Payment Entry")
            frappe.db.commit()

    def process(self):
        self.change_naming_series()

    
def execute():
    payment_entry_instance = PaymentEntryPatches()
    payment_entry_instance.process()