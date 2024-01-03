import pandas as pd
import os
import json
import frappe
import shutil
import tempfile
from frappe.utils import now

# from date import 
# defining the path of the input and out put
base_path = os.getcwd()
site_path = frappe.get_site_path()[1:]

# target_folder = 'C:/PROJECT/Agarwals/SettlementAdvice/Settlement_Dump_Procces/output/Total_uk2.xlsx'
# SITE_PATH = ''
@frappe.whitelist()
def advice_transform():

    file_details = frappe.get_all("File upload",{"status":"Open", "select_document_type": "Settlement Advice"},"*")
    for file in file_details:
        file_link = file.upload
        folder =  f"{base_path}{site_path}{file_link}"
        customer_name = file.payer_type
        parser_details = frappe.get_doc("Excel Parser",customer_name)
        mapper = parser_details.mapping
        new_mapper = json.loads(mapper)
        print("File:", file)
        if ".csv" in file_link.lower():
            df = pd.read_csv(folder,usecols=["Claim Number","Claim-Amount Claimed","Claim-Cheque Number","Claim-Transferred Amt","Claim-TDS Amt","Claim-Status","Claim-Date Of Approval"])
        else:
            df = pd.read_excel(folder)
            i = 1
            for keys in new_mapper.keys():
                for index, row in df.iterrows():
                        if keys in row.index and i == 1:
                            header_row_index = -1
                            break
                        i = 2
                        
                        if keys in row.values:
                            print(row.index)
                            header_row_index = index
                            break
                break
        df = pd.read_excel(folder , header = int(header_row_index)+1)
        columns = df.columns.values
        print(columns)
        df = df.rename(columns = new_mapper)
        print(df.columns)
        all_columns = ['claim_id','utr_number', 'settled_amount', "claim_status", "tds_amount", "paid_date", "bill_no", "claim_amount"]
        for every_column in all_columns:
            if every_column not in df.columns:
                df[every_column] = []
                
        df = df[['claim_id','utr_number', 'settled_amount', "claim_status", "tds_amount", "paid_date", "bill_no", "claim_amount"]]
        new_file_name = f'{base_path}{site_path}/private/files/DrAgarwals/Transform/{file.name}'
        df.dropna()
        new_df = format_utr(df)
        write_file_insert_record(new_df, folder,file_details,"None", new_file_name)

def write_file_insert_record(df,filename, parent_list,upload_type, new_file_name):
    is_private = 1
    upload_type = upload_type
    df.to_excel(new_file_name, engine='openpyxl')
    for every_parent in parent_list: 
        doc = frappe.get_doc("File upload",every_parent.name)
        doc.status="In Process"
        doc.append("document_reference", {
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


def format_utr(df):
    utr_list = df.fillna(0).utr_number.to_list()
    new_utr_list = []

    for item in utr_list:
        item = str(item).replace('UIIC_', 'CITIN')
        item = str(item).replace('UIC_', 'CITIN')

        if str(item).startswith('23') and len(str(item)) == 11:
            item = "CITIN" + str(item)
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

    df['utr_number'] = new_utr_list

    return df






# @frappe.whitelist()
# def data_feeder(**kwargs):
#     type = kwargs["document_type"]
#     list_to_clean = frappe.db.get_all("File upload", filters={"status":"Open", "document_type": "Settlement Advice"},fields="*")
#     for every_list in list_to_clean:
#         base_path = os.getcwd()
#         site_path = frappe.get_site_path()[1:]
#         claim_data = f"{base_path}{site_path}{every_list.upload}"
#         claim = format_utr(pd.read_excel(claim_data,engine='openpyxl'))
#         claim['utrno'] = claim.loc[:, 'utr_number']
#         # formatted_utr = format_utr(claim)
#         df=advice_transform()
#         file_name=every_list.upload.split("/")[-1]
#         write_file_insert_record(df,f"new_{file_name}",every_list.name,upload_type="New")