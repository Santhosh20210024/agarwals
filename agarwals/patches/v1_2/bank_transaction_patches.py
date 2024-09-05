import frappe
from agarwals.utils.error_handler import log_error
class BankTransactionPatches:
    def change_naming_series(self):
            custom_bank_transaction_records =[{
                'property' : 'naming_rule',
                'property_type' :'Data',
                'value' : 'By fieldname'},
                {'property' : 'autoname',
                'property_type' :'Data',
                'value' : 'field:reference_number'}]
            for record in custom_bank_transaction_records :
                try:
                    bank_tranasaction_record =frappe.new_doc('Property Setter')
                    bank_tranasaction_record.update({
                        'doctype_or_field':'DocType',
                        'doc_type':'Bank Transaction',
                        'property' : record.get('property'),
                        'property_type' : record.get('property_type'),
                        'value' : record.get('value')
                    })
                    bank_tranasaction_record.save()
                except Exception as e:
                    log_error(e,"Bank Transaction")
                
            frappe.db.commit()
            

    def process(self):
        self.change_naming_series()


def execute():
    BankTransactionInstance = BankTransactionPatches()
    BankTransactionInstance.change_naming_series()