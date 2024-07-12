# Copyright (c) 2023, Techfinite Systems and contributors
# For license information, please see license.txt

import frappe
import zipfile
import os
import pdfplumber
import json
import pandas as pd
from datetime import datetime
import re
from agarwals.utils.error_handler import log_error
from frappe.model.document import Document
from agarwals.agarwals.doctype.file_upload.file_upload import Fileupload

class PdfExtract(Document):
    pass
@frappe.whitelist()
def pdfwithtext(parent_name = None):
    folder = []
    if parent_name == None:
        pdf_extract_list = frappe.get_all("Pdf Extract",{"is_parsed": False},pluck = "name")
        for pdf_extract in pdf_extract_list:
            if folder == []:
                folder = file_list(pdf_extract)
                pdf_parsing(folder, pdf_extract)
    else:
        folder = file_list(parent_name)
        finished = pdf_parsing(folder)
        return finished


def pdf_parsing(folder, doc=None):
    try: 
        if folder:
            control_panel = frappe.get_single("Control Panel")
            data_frame = pd.DataFrame()
            today = datetime.now().strftime("%Y-%m-%d")
            for every_file in folder:
                if every_file.file_type == None or every_file.file_type.lower() not in ["pdf","zip"]:
                    log_error(f"{every_file.file_type} is not supported")
                    continue
                
                
                #set path
                base_path = os.getcwd()
                site_path = frappe.get_site_path()[1:]
                full_path = base_path+site_path
                file_name = every_file.file_url.split("/")[-1]
                pdf_file = full_path+str(every_file.file_url)
                
                #open file
                if every_file.file_type.lower() == "zip":
                    extract_folder = f"{full_path}{control_panel.pdf_path}"
                    is_folder_exist(extract_folder)
                    pdf_list = unzip_files(pdf_file, extract_folder)
                    for pdf in pdf_list:
                        pdffileobj = open(f"{extract_folder}/{pdf}", 'rb')
                        cleaned_words = read_pdf(pdffileobj)
                        data_frame, customer = process_pdf( cleaned_words, data_frame)
                else:
                    pdffileobj = open(pdf_file, 'rb')
                    cleaned_words = read_pdf(pdffileobj)
                    data_frame, customer = process_pdf(cleaned_words, data_frame)
                    
                #write cleaned words in pdf text
                if customer == None:
                    pdf_text = frappe.new_doc("Parsed Text")
                    pdf_text.pdf_text = cleaned_words
                    pdf_text.save()
                    break
                
            if customer != None:
                
                customer_name = frappe.get_all("Pdf Parser",{"tpa_name":customer},pluck= "customer")[0]
                #set Path
                is_folder_exist(f"{full_path}{control_panel.pdf_path}")
                full_file_path = f"{full_path}{control_panel.pdf_path}/pp-{customer_name}.csv"
                file_path = f"{control_panel.pdf_path}/pp-{customer_name}.csv"
                
                
                data_frame.to_csv(full_file_path, index=False)
                file_url = create_file_doc(full_file_path, file_path)
                create_fileupload(file_url,doc,customer_name, today)
                return True
    except Exception as e:
        log_error(e)
        
        
        
def create_file_doc(full_file_path, file_path):
    file_name = full_file_path.split('/')[-1]
    file = frappe.new_doc('File')
    file.set('file_name', file_name)
    file.set('is_private', 1)
    file.set('file_url',file_path)
    file.save()
    frappe.db.commit()
    return file.file_url
    
                    
def read_pdf(pdffileobj):
            #read pdf
        text = None
        pdfreader = pdfplumber.open(pdffileobj)
        x = len(pdfreader.pages)
        for i in range(x):
            page_obj = pdfreader.pages[i]
            if text != None:
                text += page_obj.extract_text()
            else:
                text = page_obj.extract_text()
        cleaned_words = new_line(text)
        return cleaned_words
        
        
def process_pdf(cleaned_words, data_frame):
        customer_list = []
        customers = frappe.get_all("Pdf Parser",{},["tpa_name","customer","mapping"])
        for every_customer in customers:
            customer_list.append(every_customer.tpa_name)
        customer = get_tpa_name(customer_list, cleaned_words)
        json_data = get_sa_values(customer, cleaned_words,"Pdf Parser")
        data_frame = process_dataframe(json_data, data_frame)
        return data_frame, customer
            

def file_list(parent_name):
    if parent_name:
        folder = frappe.get_all("File", {"attached_to_name": parent_name}, ["file_url", "file_name", "file_type"])
    return folder
        

def match(word, position, cleaned_words):
    match = re.search(word,cleaned_words)
    split_pos = str(position).split(",")
    for pos in split_pos:
        if match:
            result = match.group(int(pos))
            if result:
                return result
            else:
                log_error("there are no result for this match")
        else:
            log_error("There are no match for this pattern")


@frappe.whitelist()
def new_line(text):
    new_line = None
    for char in text:
        if char in ["\n","\r","\t"]:
            if new_line == None:
                new_line = " "
            else:
                new_line += " "
        else:
            if new_line == None:
                new_line = "".join(char)
            else:
                new_line += "".join(char)

    return new_line


def get_tpa_name(customer_list, text):
    try:
        for every_customer_name in customer_list:
            if every_customer_name in text:
                customer = every_customer_name
                return customer
    except Exception as e:
        log_error(e)



def get_sa_values(customer, cleaned_words,doctype):
    try:
        tpa_doc = frappe.get_doc(doctype, {"tpa_name": customer}, ["mapping"])
        tpa_json = tpa_doc.mapping
        data = json.loads(tpa_json)
        date_format = tpa_doc.date_format
        json_data = {}
        json_data["name"] = [customer]
        for key, values in data.items():
            if key == "claim_number":
                claim_number = match(values["search"], values["index"], cleaned_words)
                json_data["claim_number"] = [claim_number]
            elif key == "settled_amount":
                settled_amount = match(values["search"], values["index"], cleaned_words)
                settled_amount = remove_comma(settled_amount)
                json_data["settled_amount"] = [int(settled_amount)]
            elif key == "utr":
                transaction_number = match(values["search"], values["index"], cleaned_words)
                json_data["utr_number"] = [transaction_number]
            elif key == "tds":
                tds = match(values["search"], values["index"], cleaned_words)
                tds = remove_comma(tds)
                json_data["tds_amount"] = [int(tds)]
            elif key == "deductions":
                deductions = match(values["search"], values["index"], cleaned_words)
                deductions = remove_comma(deductions)
                json_data["deduction"] = [int(deductions)]
            elif key == "paid_date":
                paid_date = match(values["search"], values["index"], cleaned_words)
                paid_date = format_date(paid_date,date_format)
                json_data["paid_date"] = [paid_date]
        return json_data
    except Exception as e:

        log_error(e)


def remove_comma(value):
    if "," in value:
        output_value = value.replace(",", "")
    else:
        output_value = value
        
    if "." in output_value:
        output_value = output_value.split(".")[0]
    else:
        output_value = value
    return output_value


def unzip_files(fpath= None, fdir= None):
    try:
        if os.path.exists(fpath):
            with zipfile.ZipFile(fpath) as _zip:
                zip_list = _zip.namelist()
                is_folder_exist(fdir)
                _zip.extractall(fdir)
                return zip_list
        else:
            frappe.throw("The corresponding zip file is not found on the specified location")
            return False
    except Exception as e:
        log_error('File upload', str(e))
        frappe.throw('Error while processing the zip files')
        
        
def is_folder_exist(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
        
def format_date(paid_date, date_format):
    try:
        formatted_date = datetime.strptime(paid_date,date_format)
        return formatted_date
    except Exception as e :
        log_error(str(e))
        
        
def process_dataframe(json_data, data_frame):
        new_data = pd.DataFrame(json_data)
        data_frame = data_frame._append(new_data, ignore_index = True)    
        return data_frame
    
    
def create_fileupload(file_url,file_list,customer_name, today):
    file_upload_doc=frappe.new_doc("File upload")
    file_upload_doc.document_type= "Settlement Advice"
    file_upload_doc.payer_type= customer_name
    file_upload_doc.upload= file_url
    file_upload_doc.is_email= 1
    file_upload_doc.file_format= 'EXCEL'
    
    if file_list:
        update_file = frappe.get_doc("Pdf Extract", file_list)
        update_file.is_parsed = True
        update_file.parsed_date = today
        update_file.save()
        file_upload_doc.is_bot = 1
    
    file_upload_doc.save(ignore_permissions=True)
    frappe.db.commit()