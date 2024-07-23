import frappe
import math
from agarwals.utils.error_handler import log_error

@frappe.whitelist()
def load_data():
	try:
		repo_doc = frappe.get_doc('Report','25. Bank Statement Balance')
		query = repo_doc.query
		accounts = frappe.db.sql(query,as_dict = True)
		
		for account in accounts:
			close_docs=frappe.get_all('Closing Balance',filters={'name':account['Bank Account']})
			if close_docs:	
				update_existing(account)		
			else:
				create_close_doc(account)
	except Exception as e:
		log_error(str(e),'Closing Balance')
  
@frappe.whitelist()        	
def validate():
	close_docs=frappe.get_all('Closing Balance')
	for close_doc in close_docs:
		doc=frappe.get_doc('Closing Balance',close_doc.name)
		doc.difference = doc.closing_balance - round(doc.ag_closing_balance)
		doc.save()
		frappe.db.commit()

def create_close_doc(account):
	doc=frappe.new_doc('Closing Balance')
	doc.bank_account=account['Bank Account']
	doc.opening_balance=account['Opening Balance']
	doc.deposit=account['Deposit']
	doc.withdrawal=account['Withdrawal']
	doc.closing_balance=account['Closing Balance']
	doc.save()
	frappe.db.commit()

def update_existing(account):
	doc=frappe.get_doc('Closing Balance',account['Bank Account'])
	doc.opening_balance=account['Opening Balance']
	doc.deposit=account['Deposit']
	doc.withdrawal=account['Withdrawal']
	doc.closing_balance=account['Closing Balance']
	doc.save()
	frappe.db.commit()
 
def validate_balance():
	load_data()
	validate()
	balance_list = frappe.get_all('Closing Balance',fields = {'name','closing_balance','ag_closing_balance','difference'})
	mail = frappe.db.get_single_value('Control Panel','mail_id')
	balance = frappe.get_list('Closing Balance',filters={'difference':['!=',0],'skip':0},fields = 'difference')
	mail_ids = mail.split(',')
	
	if len(balance) > 1:
		html_table = format_table(balance_list)
		frappe.sendmail(mail_ids,subject = "Closing Balance Check Regarding " , message = f"""
                <p>Dear User,</p>
                <p>Please check the closing balance  details:</p>
                {html_table}
                <p>Regards,<br>Your Company</p>
            """)
		frappe.throw('Check the closing balance')
		


def format_table(balance_list):
    html = "<table border='1'>"
    html += "<tr>"
    
    for key in balance_list[0].keys():
        html += f"<th>{key}</th>"
    html += "</tr>"
    
    for record in balance_list:
        html += "<tr>"
        for value in record.values():
            html += f"<td>{value}</td>"
        html += "</tr>"
    
    html += "</table>"
    return html