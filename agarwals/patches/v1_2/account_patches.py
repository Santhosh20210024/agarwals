import frappe 
from agarwals.utils.error_handler import log_error
from agarwals.utils.accounting_utils import get_abbr
class AccountPatches:
    def create_records(self):
        record_list = [{'account_name' : "TDS",'parent_account' : 'Duties and Taxes - A'},{'account_name' : "Disallowance",'parent_account' : 'Current Liabilities - A'}]
        abbrevation = get_abbr()
        for record in record_list :
            try:
                doc_name = f"{record.get('account_name')} - {abbrevation}"
                if not frappe.db.exists("Account", doc_name):
                    account_record = frappe.new_doc('Account')
                    account_record.update({
                        'account_name' : record.get('account_name'),
                        'parent_account' : record.get('parent_account')
                    })
                    account_record.save()
                frappe.db.commit()
            except Exception as e:
                    log_error(e , "Account")
        
    def process(self):
        self.create_records()
        
    
def execute():
    account_instance = AccountPatches()
    account_instance.process()    
