import pandas as pd
import os
import frappe
from datetime import date
from agarwals.utils.loader import Loader
import hashlib

SITE_PATH = frappe.get_single('Control Panel').site_path

def left_join(source_df,target_df):
    left_on, right_on = "hash","hash"
    merged_df = source_df.merge(target_df, left_on=left_on, right_on=right_on, how='left',
                                        indicator=True,
                                        suffixes=('', '_x'))
    return merged_df

def hashing_job(source_df):
    source_df['hash_column'] = ''
    columns_to_hash = ["claim_id","bill_number","utr_number","claim_status","claim_amount","disallowed_amount","payers_remark","settled_amount","tds_amount","paid_date"]
    for column in columns_to_hash:
        source_df['hash_column'] = source_df['hash_column'].astype(str) + source_df[column].astype(str)
    source_df['hash'] = source_df['hash_column'].apply(lambda x: hashlib.sha1(x.encode('utf-8')).hexdigest())
    return source_df

def get_target_df():
        query = f"""
                      SELECT 
                          hash
                      FROM 
                          `tabSettlement Advice Staging`
                      """
        records = frappe.db.sql(query, as_list=True)
        return pd.DataFrame(records, columns=['hash'])

def clean_header(list_to_clean,list_of_char_to_repalce):
    cleaned_list=[]
    for header in list_to_clean:
        for char_to_replace in list_of_char_to_repalce:
            header=str(header).replace(char_to_replace,"").lower()
        cleaned_list.append(header)
    return cleaned_list

def format_date(df,date_formats,date_column):
    df['original_date'] = df[date_column].astype(str).apply(lambda x: x.strip() if isinstance(x,str) else x)
    df['formatted_date'] = pd.NaT
    for fmt in date_formats:
        new_column = 'date_' + fmt.replace('%','').replace('/','_').replace(':','').replace(' ','_')
        df[new_column] = pd.to_datetime(df['original_date'],format = fmt, errors='coerce')
        df['formatted_date'] = df['formatted_date'].combine_first(df[new_column])
    df[date_column] = df['formatted_date']
    df = prune_columns(df,[col for col in df.columns if 'date_' in col or col == 'formatted_date' or col == 'original_date'])
    return df

def prune_columns(df, columns_to_prune):
    df = df.drop(columns=columns_to_prune, errors='ignore')
    return df 

def swap_advice_amount(row):
    row['settled_amount'] = pd.to_numeric(row['settled_amount'])
    row['tds_amount'] = pd.to_numeric(row['tds_amount'])

    if row['settled_amount'] < row['tds_amount']:
        temp = row['settled_amount']
        row['settled_amount'] = row['tds_amount']
        row['tds_amount'] = temp
    return row

def check_advice_amount(df):
    df = df.apply(swap_advice_amount, axis=1)
    return df

def clean_data(df):
        df["final_utr_number"]=df["utr_number"].fillna("0").astype(str).str.lstrip("0").str.strip().replace(r"[\"\'?]", '',regex=True).replace("NOT AVAILABLE","0").replace("","0")
        df["claim_id"]=df["claim_id"].fillna("0").astype(str).str.strip().replace(r"[\"\'?]", '',regex=True).replace("","0")
        df = format_date(df,eval(frappe.get_single('Bank Configuration').date_formats),'paid_date')
        format_utr(df)
        return df
        
def update_status(doctype, name, status):
        if doctype == 'File upload':
            doc = frappe.get_doc('File upload',name)
            doc.status = status 
            doc.save()
            frappe.db.commit()
        else:
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

def move_to_transform(file, df, type, folder, prune=True, status = 'Open'):
    if df.empty:
        return None
    if prune:
        df = prune_columns(df,['name', '_merge', 'hash_x', 'hash_column'])
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
        utr_list = source_df.fillna(0).final_utr_number.to_list()
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

        source_df['final_utr_number'] = new_utr_list

def log_error(doctype_name, reference_name, error_message):
    error_log = frappe.new_doc('Error Record Log')
    error_log.set('doctype_name', doctype_name)
    error_log.set('reference_name', reference_name)
    error_log.set('error_message', error_message)
    error_log.save()

def split_and_move_to_transform(source_df,file):
    source_df=hashing_job(source_df)
    target_df=get_target_df()
    if target_df.empty: 
            new_records = source_df 
            move_to_transform(file, new_records, 'Insert', 'Transform', False)
    else:
            merged_df=left_join(source_df,target_df)
            if merged_df.empty:
                return False
            new_records = merged_df[merged_df['_merge'] == 'left_only']
            existing_df = merged_df[merged_df['_merge'] == 'both']
            move_to_transform(file, new_records, 'Insert', 'Transform', True)
            move_to_transform(file, existing_df, 'Skip', 'Bin', True, 'Skipped')

@frappe.whitelist()
def advice_transform():
        file_list_details = frappe.get_all("File upload",{"status":"Open", "document_type": "Settlement Advice"},"*")
        for file in file_list_details:
            try:
                update_status('File upload', file.name, 'In Process')
                file_link = file.upload
                file_url_to_read =  SITE_PATH+file_link
                config = frappe.get_doc("Settlement Advice Configuration")
                header_row_patterns = eval(config.header_row_patterns)
                list_of_char_to_repalce = eval(config.char_to_replace_in_header)
                header_row_patterns = clean_header(header_row_patterns,list_of_char_to_repalce)
                target_columns = eval(config.target_columns)
                
                if ".csv" in file_link.lower():
                    df = pd.read_csv(file_url_to_read)
                    file_link=file_link.lower().replace(".csv",".xlsx")
                else:
                    df = pd.read_excel(file_url_to_read,header=None,)
                    break_loop=False
                    
                    for keys in header_row_patterns:  # header skip
                        if break_loop:
                            break
                        header_row_index = None
                        for index, row in df.iterrows():
                            if keys in clean_header(row.values,list_of_char_to_repalce):
                                header_row_index = index
                                break_loop=True
                                break 
                    
                    df = pd.read_excel(file_url_to_read , header = header_row_index)
                df.columns = clean_header(df.columns.values,list_of_char_to_repalce)
                column_list = df.columns.values
                rename_value={}
                for key,value in target_columns.items():
                    if isinstance(value[0],list):
                        p1_list=clean_header(value[0],list_of_char_to_repalce)
                        p2_list=clean_header(value[1],list_of_char_to_repalce)
                    else:
                        p1_list=clean_header(value,list_of_char_to_repalce)
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
                    log_error('Settlement Advice Staging',file.name,"No Valid data header or file is empty")
                    update_status('File upload', file.name, 'Error')
                    frappe.db.commit()
                    continue
                all_columns = list(target_columns.keys())
                all_columns.append("final_utr_number")
                for every_column in all_columns:
                    if every_column not in df.columns:
                        df[every_column] = ""         
                df = df[all_columns]
                df["source"]=file.name
                df = clean_data(df)
                # Amount checking
                df = check_advice_amount(df)
                split_and_move_to_transform(df,file)  
                loader = Loader("Settlement Advice Staging")
                loader.process()
                update_parent_status(file)
            except Exception as e:
                log_error('Settlement Advice Staging',file.name,e)
                update_status('File upload', file.name, 'Error')
                frappe.db.commit()
                continue
        return "Success"