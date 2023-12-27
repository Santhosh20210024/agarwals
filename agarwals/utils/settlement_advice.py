import pandas as pd
import os
import json
# defining the path of the input and out put
folder = 'C:/PROJECT/Agarwals/SettlementAdvice/Settlement_Dump_Procces/unprocesssed file/unknown/f2/'
target_folder = 'C:/PROJECT/Agarwals/SettlementAdvice/Settlement_Dump_Procces/output/Total_uk2.xlsx'

def advice_transform():
    json={"Mediassist India Tpa P Ltd":{"columns":{"Claim Number": "claim_id",
                                    "Claimed Amount": "claim_amount",
                                    "Cheque/ NEFT/ UTR No.":"utr_number",
                                    "Settled Amount":"settled_amount",
                                    "TDS Amount":"tds_amount","Claim Status":"claim_status","Payment Update Date":"paid_date"},"index_col":1},
          "ICIC":{"Claim Number": "claim_id",
                                    "Claim-Amount Claimed": "claim_amount",
                                    "Claim-Cheque Number":"utr_number",
                                    "Claim-Transferred Amt":"settled_amount",
                                    "Claim-TDS Amt":"tds_amount",
                                    "Claim-Status":"claim_status",
                                    "Claim-Date Of Approval":"paid_date"},
          "Star Health": {"Claim ID": "claim_id",
                    "Claim Amount": "claim_amount",
                    "UTR": "utr_number",
                    "Claim Net Pay Amount": "settled_amount",
                    "T.D.S.": "tds_amount",
                    "Status Name": "claim_status",
                    "Settlement Date": "paid_date"},
          "bajaj": {"CLAIM NO": "claim_id",
                    "NET AMOUNT": "claim_amount",
                          "UTR NO": "utr_number",
                          "GROSS AMOUNT": "settled_amount",
                          "TDS AMOUNT": "tds_amount",
                          "TRANSFER DATE": "paid_date"},
          "Health India": {"CCN": "claim_id",
                    "Intimated Amount": "claim_amount",
                    "utrnumber": "utr_number",
                    "SettledAmount": "settled_amount",
                    "Claim Status":"claim_status",
                    "utrdate": "paid_date"},
          "MD India": {"CCNNumber": "claim_id",
                           "Settled_Amount": "claim_amount",
                           "Cheque_No": "utr_number",
                           "Paid_Amount": "settled_amount",
                           "TDS_Amount":"tds_amount",
                           "cheque_date": "paid_date"},
          "paramount": {"FIR": "claim_id",
                           "AL_AMOUNT": "claim_amount",
                           "UTR_NO": "utr_number",
                           "AMOUNT_PAID": "settled_amount",
                           "TDS_AMT":"tds_amount",
                            "STATUS":"claim_status",
                           "DT_OF_PAYMENT": "paid_date"},
          "Rohini":{"Claim Number":"claim_id",
                           "Claimed Amount": "claim_amount",
                           "Map Cheque/NEFT Number": "utr_number",
                           "Total Amount Paid": "settled_amount",
                           "TDS amount":"tds_amount",
                            "Final Status":"claim_status",
                           "Map Cheque/NEFT Date": "paid_date"},
          "uk2":{"CCNNumber":"claim_id",
                          "UTR_No": "utr_number",
                           "Approved Amount": "settled_amount",
                           "UTR_Dt": "paid_date"},}
    clm_vlaues=json["uk2"]


    # Get the list of all files and directories
    dir_list = os.listdir(folder)

    print("Files and directories in '", folder, "' :")

    # prints all files
    # print(dir_list)
    total_df=pd.DataFrame()
    for file in dir_list:
        print("File:", file )
        if ".csv" in file.lower():
            df = pd.read_csv(folder + file,usecols=["Claim Number","Claim-Amount Claimed","Claim-Cheque Number","Claim-Transferred Amt","Claim-TDS Amt","Claim-Status","Claim-Date Of Approval"])
            # df = pd.read_csv(folder + file)
        else:
            # df = pd.read_excel(folder + file,header=2)
            df = pd.read_excel(folder + file)
        columns = df.columns.values
        # if 'Sum of Settled Amount' in columns:
        #     df = df.rename(columns = {'Sum of Settled Amount':'Settled Amount','Sum of TDS Amount':"TDS Amount","Sum of Claimed Amount":"Claimed Amount"})
        print(df.columns)
        df=df.rename(columns=clm_vlaues)
        # df = df[df["claim_status"] == "Claim Paid"]
        df = df[['claim_id','utr_number', 'settled_amount',"paid_date"]]
        # df = df[['claim_id', 'claim_amount', 'utr_number', 'settled_amount',"paid_date"]]
        total_df=pd.concat([total_df,df],axis=0)

    total_df.dropna()
    print(sum(total_df['settled_amount']))
    format_utr(total_df)
    print(len(total_df))
    total_df.to_excel(target_folder,index=False)

    # print(total_df)
    # print(sum(total_df['Settled Amount']))


    #total_claimbook_df = pd.read_excel(TOTAL_CLAIMBOOK)
    #existing_claimbook_in_db = pd.read_excel(EXISTING_CLAIMBOOK_IN_DB)


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

def write_file_insert_record(df,filename, parent_field_id,upload_type):
    is_private = 1
    file_url = f"{SITE_PATH}/private/files/{filename}"
    folder = "Home/DrAgarwals/Transform"
    upload_type=upload_type
    # Create a temporary XLSX file
    with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmpfile:
        excel_file_path = tmpfile.name
        df.to_excel(excel_file_path, index=False, engine='openpyxl')

        shutil.copy(excel_file_path, file_url)

        frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "folder": folder,
            "file_url": "https://{file_url}",
            "is_private": is_private
        }).insert()
        
    doc = frappe.get_doc("File upload",parent_field_id)
    doc.status="In Process"
    doc.append("document_reference", {
        "date": date.today(),
        "document_type": doc.select_document_type,
        "status": "In Process",
        "file_url": file_url,
        "upload_type":upload_type,
    })
    doc.save(ignore_permissions=True)
    doc.reload()

advice_transform()


@frappe.whitelist()
def data_feeder(**kwargs):
    type = kwargs["document_type"]
    list_to_clean = frappe.db.get_all("File upload", filters={"document_type": type,
                                                              "status": "Open"},
                                      fields=["upload", "name"])
    for every_list in list_to_clean:
        base_path = os.getcwd()
        site_path = frappe.get_site_path()[1:]
        claim_data = f"{base_path}{site_path}{every_list.upload}"
        claim = format_utr(pd.read_excel(claim_data,engine='openpyxl'))
        claim['utrno'] = claim.loc[:, 'utr_number']
        formatted_utr = format_utr(claim)
        file_name=every_list.upload.split("/")[-1]
        write_file_insert_record(formatted_utr,f"new_{file_name}",every_list.name,upload_type="New")