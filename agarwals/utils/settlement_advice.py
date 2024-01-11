import pandas as pd
import os
import frappe
from datetime import date
from agarwals.utils.loader import Loader
from agarwals.utils.path_data import SITE_PATH
# defining the path of the input and output
base_path = os.getcwd()
site_path = frappe.get_site_path()[1:]

def clean_header(list_to_clean):
    
    cleaned_list=[]
    list_of_char_to_repalce=[" ","-","/","_","\'","\""]
    for header in list_to_clean:
        for char_to_replace in list_of_char_to_repalce:
            header=str(header).replace(char_to_replace,"").lower()
        cleaned_list.append(header)
    return cleaned_list
    
def clean_data(df):
        df["utr_number"]=df["utr_number"].fillna("0")
        df["claim_id"]=df["claim_id"].fillna("0")
        df["utr_number"]=df["utr_number"].astype(str).str.replace(r"[\"\'^(0+)]", '',regex=True)
        df["claim_id"]=df["claim_id"].astype(str).str.replace(r"[\"\']", '',regex=True)
        df["utr_number"]=df["utr_number"].astype(str).str.strip().replace("NOT AVAILABLE","0")
        df["claim_id"]=df["claim_id"].astype(str).str.strip()
        format_utr(df)
        
        
        
def update_status(doctype, name, status):
    frappe.db.set_value(doctype,name,'status',status)
    frappe.db.commit()
    
def update_parent_status(file):
    file_record = frappe.get_doc('File upload',file.name)
    transform_records = file_record.transform
    transform_record_status = []
    for transform_record in transform_records:
        transform_record_status.append(transform_record.status)
    if "Error" in transform_record_status:
        update_status('File upload',file.name,'Error')
    elif "Partial Success" in transform_record_status:
        update_status('File upload', file.name, 'Partial Success')
    else:
        update_status('File upload', file.name, 'Success')
        
def write_excel(df, file_path, type, target_folder):
    excel_file_path = file_path.replace(file_path.split('.')[-1],'xlsx')
    file_path = excel_file_path.replace('Extract', target_folder).replace('.xlsx','_' + type + '.xlsx')
    file_path_to_write = SITE_PATH + file_path
    df.to_excel(file_path_to_write, index=False)
    return file_path

def create_file_record(file_url,folder):
    FOLDER = "Home/DrAgarwals/"
    file_name = file_url.split('/')[-1]
    file = frappe.new_doc('File')
    file.set('file_name', file_name)
    file.set('is_private', 1)
    file.set('folder', FOLDER + folder)
    file.set('file_url', file_url)
    file.save()
    frappe.db.set_value('File',file.name,'file_url',file_url)

def insert_in_file_upload(file_url, file_upload_name, type, status):
    file_upload = frappe.get_doc('File upload', file_upload_name)
    file_upload.append('transform',
                        {
                            'date': date.today(),
                            'document_type': "Settlement Advice Staging",
                            'type': type,
                            'file_url': file_url,
                            'status': status
                        })
    file_upload.save(ignore_permissions=True)

def move_to_transform(file, df, type, folder, status = 'Open'):
    if df.empty:
        return None
    file_path = write_excel(df, file.upload, type,folder)
    create_file_record(file_path,folder)
    insert_in_file_upload(file_path, file.name, type, status)

def remove_x(item):
    if "XXXXXXX" in str(item):
        return item.replace("XXXXXXX", '')
    elif "XX" in str(item) and len(item) > 16:
        return item.replace("XX", '')
    return item


def format_utr(source_df):
        utr_list = source_df.fillna(0).utr_number.to_list()
        new_utr_list = []
        for item in utr_list:
            item = str(item).replace('UIIC_', 'CITIN')
            item = str(item).replace('UIC_', 'CITIN')

            if str(item).startswith('23') and len(str(item)) == 11:
                item = "CITIN" + str(item)
                new_utr_list.append(item)
            elif len(str(item)) == 9:
                item = 'AXISCN0' + str(item)
                new_utr_list.append(item)
            elif '/' in str(item) and len(item.split('/')) == 2:
                item = item.split('/')[1]
                if '-' in str(item):
                    item = item.split('-')
                    new_utr_list.append(item[-1])
                else:
                    new_utr_list.append(remove_x(item))
            elif '-' in str(item):
                item = item.split('-')
                new_utr_list.append(remove_x(item[-1]))
            else:
                new_utr_list.append(remove_x(item))

        source_df['utr_number'] = new_utr_list

def log_error(doctype_name, reference_name, error_message):
    error_log = frappe.new_doc('Error Record Log')
    error_log.set('doctype_name', doctype_name)
    error_log.set('reference_name', reference_name)
    error_log.set('error_message', error_message)
    error_log.save()

@frappe.whitelist()
def advice_transform():
        file_list_details = frappe.get_all("File upload",{"status":"Open", "document_type": "Settlement Advice"},"*")
        for file in file_list_details:
            try:
                update_status('File upload', file.name, 'In Process')
                file_link = file.upload
                file_url_to_read =  f"{base_path}{site_path}{file_link}"
                config = frappe.get_doc("Settlement Advice Configuration")
                header_row_patterns = eval(config.header_row_patterns)
                header_row_patterns = clean_header(header_row_patterns)
                target_columns = eval(config.target_columns)
                if ".csv" in file_link.lower():
                    df = pd.read_csv(file_url_to_read)
                    file_link=file_link.lower().replace(".csv",".xlsx")
                else:
                    df = pd.read_excel(file_url_to_read,header=None,)
                    break_loop=False
                    for keys in header_row_patterns: 
                        if break_loop:
                            break
                        header_row_index = None
                        for index,row in df.iterrows():
                            if keys in clean_header(row.values):
                                header_row_index = index
                                break_loop=True
                                break 
                    
                    df = pd.read_excel(file_url_to_read , header = header_row_index)
                df.columns = clean_header(df.columns.values)
                column_list = df.columns.values
                rename_value={}
                for key,value in target_columns.items():
                    if isinstance(value[0],list):
                        p1_list=clean_header(value[0])
                        p2_list=clean_header(value[1])
                    else:
                        p1_list=clean_header(value)
                        p2_list=[]
                    i=0
                    for columns in p1_list:
                        if columns in column_list:
                            rename_value[columns]=key
                            i+=1
                            break
                    if i==0 and p2_list is not None:
                        for columns in p2_list:
                            if columns in column_list:
                                rename_value[columns]=key
                                break
                df = df.rename(columns = rename_value)
                if "claim_id" not in df.columns:
                    log_error('Settlement Advice Staging',file.name,"No Valid data or file is empty")
                    update_status('File upload', file.name, 'Error')
                    frappe.db.commit()
                    continue
                all_columns = target_columns.keys()
                for every_column in all_columns:
                    if every_column not in df.columns:
                        df[every_column] = ""         
                df = df[all_columns]
                df["source"]=file.name
                clean_data(df)
                move_to_transform(file, df, 'Insert', 'Transform')
                loader = Loader("Settlement Advice Staging")
                loader.process()
                update_parent_status(file)
            except Exception as e:
                log_error('Settlement Advice Staging',file.name,e)
                update_status('File upload', file.name, 'Error')
                frappe.db.commit()
                continue
        return "Success"