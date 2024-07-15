# Copyright (c) 2024, Techfinite Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from bs4 import BeautifulSoup
from agarwals.utils.pdf_parsing import get_tpa_name,get_sa_values,new_line,pdfwithtext,is_folder_exist,create_file_doc, create_fileupload,process_dataframe
from frappe.email.inbox import mark_as_trash, mark_as_closed_open
from agarwals.utils.error_handler import log_error
import pandas as pd
import os
from datetime import datetime
import sys

class EmailExtract(Document):
	pass

@frappe.whitelist()
def email_parsing():
	doc = None
	customer = None
	row_count=1 #for checking the null cut off email eg: Not needed char -- needed char -- needed char then  it will use this to return continue
	row_count_buffer=1 # this is used to get the exact count of row_count after row_count changed to  continue
	file_count=0 # this is used to name the file
	data_frame = pd.DataFrame()

	#initialize
	_base_path,_site_path,full_path,customer_name,today,control_panel = _init()
	#get_email_documents
	email_to_parse = get_parsing_email()
	if email_to_parse != None:
		for email in email_to_parse:
			try:
				file_count+=1
				email_contents =  email.text_content
				email_contents = delimitter_type(email_contents, control_panel)[0]
				#check and change the html to text.
				for email_content in email_contents:
						text = new_line(email_content)
		
						#text parsing
						if text:
							row_count,row_count_buffer,data_frame,customer,pdf_finished = text_parsing(text,customer_name,email,row_count,row_count_buffer,data_frame,customer)
							if pdf_finished:
								break
							if row_count == 0:
								break
							elif row_count == "continue":
								row_count = row_count_buffer
								row_count_buffer = 1
								continue
				try:
					if pdf_finished == False:
						total_size= data_frame.claim_number.size
						original_customer_name = frappe.get_all("Email Parser",{"tpa_name":customer},pluck= "customer")[0]
						is_folder_exist(f"{full_path}{control_panel.email_path}")
						full_file_path = f"{full_path}{control_panel.email_path}/ep-{original_customer_name}-{str(file_count)}-{str(row_count)}.csv"
						file_path = f"{control_panel.email_path}/ep-{original_customer_name}-{str(file_count)}-{str(row_count)}.csv"
						#file creation
						data_frame.to_csv(full_file_path, index=False)
						file_url = create_file_doc(full_file_path, file_path)
						create_fileupload(file_url,doc,original_customer_name, today)
						mark_as_closed_open(email.name,"Closed")
				except:
					log_error(f"Email does not contain customer, Please check the Email Parsing for the customer, email Id:{email.name}")
			except Exception as e:
				log_error(e)



def text_parsing(text,customer_name,email,row_count,row_count_buffer,data_frame,customer):
	finished = False
	try:
			customer_list = frappe.get_all("Email Parser",{},["*"])
			for every_customer in customer_list:
				customer_name.append(every_customer.tpa_name)
			customer = get_tpa_name(customer_name, text)
			if customer:
				json_data = get_sa_values(customer, text,"Email Parser")
				data_frame = process_dataframe(json_data,data_frame)
				#file path
				row_count+=1
				return row_count,row_count_buffer,data_frame,customer,finished
			else:
				if email.has_attachment:
					finished = pdfwithtext(email.name)
					if finished:
						mark_as_closed_open(email.name,"Closed")
				else:
					row_count = "continue"
					row_count_buffer = 1
				return row_count,row_count_buffer,data_frame,customer,finished

	except Exception as e:
			if email.has_attachments:
				log_error(e)
			else:
				parsed_text_update(text,"Email")
				frappe.msgprint("No customer detected")
				return False
    
    
    

		
def _init():
	base_path = os.getcwd()
	site_path = frappe.get_site_path()[1:]
	full_path = base_path + site_path
	customer_name = []
	today = datetime.now()
	control_panel = frappe.get_single('Control Panel')
	return base_path,site_path,full_path,customer_name,today,control_panel


def get_parsing_email():
	control_panel = frappe.get_single('Control Panel')
	email_list = frappe.get_all("Communication", filters = {"status":"Open", "sent_or_received":"Received","email_account":control_panel.recipients},fields = ["*"])
	if email_list:
		return email_list
	else:
		return None


def parsed_text_update(text, type):
    parsed_doc = frappe.get_single("Parsed Text")
    if type == "Email":
        parsed_doc.email_text = text
    else:
        parsed_doc.pdf_text = text
    parsed_doc.save()
    
    
@frappe.whitelist()
def segrigate_email(*args, **kwargs):
	try:
		email_to_parse = []
		inclusion_text = frappe.get_all("Inclusion Email Text",{"type":"subject"},pluck="name")#settlement advice email patterns
		control_panel = frappe.get_single('Control Panel')
		email_list = frappe.get_all("Communication", filters = {"email_account":control_panel.recipients,"communication_type":"Communication","communication_medium":"Email","status":"Open","email_status":["in",["Open","Spam"]],"sent_or_received":"Received"},fields = ["*"])
		if email_list:
			#the below code can also be written like this
			#email_to_parse = [email for email in email_list if (text in email.subject for text in inclusion_text)]
			for email in email_list:
				for text in inclusion_text:
					if text in email.subject:
						email_to_parse.append(email.name)
						continue
	
			for each_mail in email_list:
				email = frappe.get_doc("Communication",each_mail.name)
				if each_mail.name not in email_to_parse:
					email.email_status = "Trash"
				else:
					email.email_status = "Open"
				email.save()
				frappe.db.commit()
					
	except Exception as e:
		log_error(e)
	
    
def delimitter_type(email_contents, control_panel):
	try:
		email_contents = email_contents.split(control_panel.delimitter)
		with_delimitter = True
	except:
		email_contents = email_contents
		with_delimitter = False
	return email_contents, with_delimitter


def parse_html(email_content):
	soup = BeautifulSoup(email_content,features="lxml")
	for script in soup(["script", "style"]):
		script.extract()
	text = soup.get_text()
	lines = (line.strip() for line in text.splitlines())
	chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
	text = '\n'.join(chunk for chunk in chunks if chunk)
	return text
