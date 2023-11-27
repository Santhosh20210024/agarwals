import frappe
@frappe.whitelist()
def import_bank_statement(bank_account,bank,attached_file):
    try:
        company = frappe.defaults.get_user_default('Company')
        bank_import = frappe.new_doc('Bank Statement Import')
        bank_import.set('company', company)
        bank_import.set('bank_account', bank_account)
        bank_import.set('bank', bank)
        bank_import.save()
        bank_import.set('import_file', attached_file)
        bank_import.save()
        bank_import.start_import()
        return "Success"
    except Exception as e:
        return e


@frappe.whitelist()
def create_sales_invoice(sales_invoice_field_and_value):
    try:
        sales_invoice = frappe.new_doc('Sales Invoice')
        for field, value in sales_invoice_field_and_value.items():
            sales_invoice.set(field, value)
        sales_invoice.save()
        sales_invoice.submit()
        return "Success"
    except Exception as e:
        return e