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
        return "File Successfully Imported"
    except:
        return "Failed to Import the File"
