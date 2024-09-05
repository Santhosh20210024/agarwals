import frappe
from agarwals.utils.error_handler import log_error
class SalesInvoicePatches:
    def change_naming_series(self):
        custom_sales_invoice_records =[{
                'property' : 'naming_rule',
                'property_type' :'Data',
                'value' : 'Set by user'},
                {'property' : 'autoname',
                'property_type' :'Data',
                'value' : 'prompt'}]
        for record in custom_sales_invoice_records :
            try :
                sales_invoice_record =frappe.new_doc('Property Setter')
                sales_invoice_record.update({
                    'doctype_or_field':'DocType',
                    'doc_type':'Sales Invoice',
                    'property' : record.get('property'),
                    'property_type' : record.get('property_type'),
                    'value' : record.get('value')
                })
                sales_invoice_record.save()
            except Exception as e:
                log_error(e, "Sales Invoice")
            frappe.db.commit()

    def process(self):
        self.change_naming_series()

    
def execute():
    sales_invoice_instance = SalesInvoicePatches()
    sales_invoice_instance.process()