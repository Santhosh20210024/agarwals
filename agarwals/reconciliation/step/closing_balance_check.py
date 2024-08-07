import frappe
import math
from agarwals.utils.error_handler import log_error

class ClosingBalance:
    
    def load_data(self):
        try:
            query = frappe.get_list('Report', filters={'name' : '25. Bank Statement Balance'},pluck = 'query')[0]
            bank_accounts = frappe.db.sql(query, as_dict=True)
            for bank_account in bank_accounts:
                doc = frappe.get_doc('Closing Balance', bank_account['Bank Account'])
                doc.bank_account = bank_account['Bank Account']
                doc.opening_balance = bank_account['Opening Balance']
                doc.deposit = bank_account['Deposit']
                doc.withdrawal = bank_account['Withdrawal']
                doc.cg_closing_balance = bank_account['Closing Balance']
                doc.save()
                frappe.db.commit()
            
                
        except Exception as e:
            log_error(e, 'Closing Balance')
    
    def validate(self):
        close_docs = frappe.get_all('Closing Balance')
        for close_doc in close_docs:
            doc = frappe.get_doc('Closing Balance', close_doc.name)
            doc.difference = doc.cg_closing_balance - round(doc.ag_closing_balance)
            doc.save()
            frappe.db.commit()
        
        
    def validate_balance(self):
        self.load_data()
        self.validate()
        closing_balance_list = frappe.get_all('Closing Balance', fields=['name', 'cg_closing_balance', 'ag_closing_balance', 'difference'],filters={'difference': ['!=', 0.0],'skip' : 0})
        mail_group = frappe.get_doc('Control Panel').check_list_email_group
        recipients = frappe.get_list('Email Group Member', {'email_group': mail_group}, pluck='email')
        if recipients:
        
            if closing_balance_list:
              html_table = ClosingBalance().format_table(closing_balance_list)
              frappe.sendmail(
                recipients=recipients,
                subject="Closing Balance Check",
                message=f"""
                    <p>Hi All,</p>
                    <p>Please check the closing balance details:</p>
                    {html_table}
                    <p>Regards,<br>TechFinite Systems</p>
                """
            )
              frappe.throw('Check the closing balance')
    
    def format_table(self,balance_list):
        if not balance_list:
            return "<p>No records found</p>"
        
        html = "<table border='1' cellpadding='5' cellspacing='0'>"
        html += "<tr>"
        
        # Add headers
        for key in balance_list[0].keys():
            html += f"<th>{key}</th>"
        html += "</tr>"
        
        # Add rows
        for record in balance_list:
            html += "<tr>"
            for value in record.values():
                html += f"<td>{value}</td>"
            html += "</tr>"
        
        html += "</table>"
        return html
@frappe.whitelist()
def load():
    ClosingBalance().load_data()
    
@frappe.whitelist()
def check():
    ClosingBalance().validate()
    
