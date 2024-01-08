import pandas as pd
import os
import frappe
from frappe.utils import now

# defining the path of the input and output
base_path = os.getcwd()
site_path = frappe.get_site_path()[1:]

def clean_header(list_to_clean):
    cleaned_list=[]
    list_of_char_to_repalce=[" ","-","/","_"]
    for header in list_to_clean:
        for char_to_replace in list_of_char_to_repalce:
            header=header.replace(char_to_replace,"").lower()
        cleaned_list.append(header)
    return cleaned_list
    
def clean_data(df):
        format_utr(df)
        df["utr_number"].str.strip()
        df["claim_id"].str.strip()
        
def write_file_insert_record(df,filename, parent_list,upload_type, new_file_name):
    is_private = 1
    upload_type = upload_type
    df.to_excel(new_file_name, engine='openpyxl')
    for every_parent in parent_list: 
        doc = frappe.get_doc("File upload",every_parent.name)
        doc.status="In Process"
        doc.append("transform", {
        "date": now(),
        "document_type": doc.select_document_type,
        "status": "In Process",
        "file_url": new_file_name,
        # "upload_type":upload_type,
    	})
        doc.save(ignore_permissions=True)
        doc.reload()
        

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

@frappe.whitelist()
def advice_transform():
    file_list_details = frappe.get_all("File upload",{"status":"Open", "document_type": "Settlement Advice"},"*")
    for file in file_list_details:
        file_link = file.upload
        folder =  f"{base_path}{site_path}{file_link}"
        config = frappe.get_doc("Settlement Advice Configuration")
        header_row_patterns = eval(config.header_row_patterns)
        target_columns = eval(config.target_columns)
        if ".csv" in file_link.lower():
            df = pd.read_csv(folder)
        else:
            df = pd.read_excel(folder)
            for keys in header_row_patterns:
                header_row_index = 0
                for index,row in df.iterrows():
                    if keys in row.values:
                        header_row_index = index
                        break
                    if header_row_index==0:
                        header_row_index-=1
        
        df = pd.read_excel(folder , header = int(header_row_index)+1)
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
        all_columns = target_columns.keys()
        for every_column in all_columns:
            if every_column not in df.columns:
                df[every_column] = ""         
        df = df[all_columns]
        clean_data(df)
        new_file_name = f'{base_path}{site_path}/private/files/DrAgarwals/Transform/{file.name}'
        write_file_insert_record(df, folder,file_list_details,"None", new_file_name)
