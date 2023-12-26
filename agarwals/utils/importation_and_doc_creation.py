import json

import frappe
@frappe.whitelist()
def import_bank_statement(bank_account,bank,attached_file):
    #For Auto Importing Bank statement
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
def import_job(doctype,import_type,file_url):
    #For Auto Importing DocType
    data_import_mapping_doc = frappe.get_doc("Data Import Mapping",doctype)
    template = data_import_mapping_doc.template
    data_import_doc = frappe.new_doc("Data Import")
    data_import_doc.set('reference_doctype', doctype)
    data_import_doc.set('import_type', import_type)
    data_import_doc.set('import_file', file_url)
    data_import_doc.save()
    frappe.db.set_value("Data Import", data_import_doc.name, 'template_options', template)
    frappe.db.commit()
    try:
        data_import_doc.start_import()
    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', 'Sales Invoice')
        error_log.set('error_message', e)
        error_log.save()



@frappe.whitelist()
def create_sales_invoice(sales_invoice_field_and_value):
    #For creating Sales Invoice before saving debtors report
    sales_invoice_existing = True if len(
        frappe.get_list("Sales Invoice", filters={'name': sales_invoice_field_and_value['name']})) != 0 else False
    if not sales_invoice_existing:
        try:
            sales_invoice = frappe.new_doc('Sales Invoice')
            for field, value in sales_invoice_field_and_value.items():
                sales_invoice.set(field, value)
            sales_invoice.save()
            sales_invoice.submit()
            return "Success"
        except Exception as e:
            return e
    else:
        print("Sales Invoice Already Exist")


@frappe.whitelist()
def create_physical_claim_submission(bill_no_array):
    #For Creating Physical Claim Submission using Bulk Select and create from debtors report
    try:
        physical_claim_submission = frappe.new_doc("Physical Claim Submission")
        print(bill_no_array)
        physical_claim_submission.set('bill_list', bill_no_array)
        physical_claim_submission.save()
        return ["Success",physical_claim_submission.name]
    except Exception as e:
        return e
