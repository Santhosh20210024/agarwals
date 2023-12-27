import pandas as pd
import os
import frappe
import dask.dataframe as dd
import tempfile
import shutil
from agarwals.utils.path_data import SITE_PATH
from datetime import date

columns_to_be_hashed = ['Hospital', 'preauth_claim_id', 'mrn', 'doctor', 'department', 'case_id', 'first_name',
                        'tpa_name', 'insurance_company_name', 'tpa_member_id', 'insurance_policy_number',
                        'is_bulk_closure', 'al_number', 'cl_number', 'doa', 'dod', 'room_type', 'final_bill_number',
                        'final_bill_amount', 'claim_amount', 'current_request_type', 'requested_amount',
                        'approved_amount', 'provisional_bill_amount', 'settled_amount', 'tds_amount',
                        'tpa_shortfall_amount', 'forwarded_to_claims_date', 'courier_vendor', 'tracking_number',
                        'preauth_submitted_date_time', 'is_admitted', 'visit_type', 'case_closed_in_preauth',
                        'unique_id']


# addind up all hash strings
def hashing_job(df_to_be_hashed):
    df_to_be_hashed['hash_str'] = ""  # initializing the column Hash_str
    if columns_to_be_hashed is not None:
        for column in columns_to_be_hashed:  # itrating throgh columns
            df_to_be_hashed['hash_str'] = df_to_be_hashed['hash_str'].astype(str) + df_to_be_hashed[column].astype(
                str)  # add the string value


# droping the merged column
def drop_x(df):
    # list comprehension of the cols that end with '_x'
    to_drop = [x for x in df if x.endswith('_x')]
    df.drop(to_drop, axis=1, inplace=True)


def splitter(claim):
    # defining the path of the input and output

    # TOTAL_CLAIMBOOK = total_claimbook_url

    NEW_CLAIMBOOK = "new_file_output_url"
    UPDATED_CLAIMBOOK = "updated_file_output_url"

    # reading inut as data frame
    total_claimbook_df = claim

    existing_claimbook_in_db = pd.DataFrame(
        (frappe.db.get_list('ClaimBook', fields=columns_to_be_hashed, as_list=True)),
        columns=columns_to_be_hashed)  # input from database

    joined_df = total_claimbook_df.merge(existing_claimbook_in_db, left_on='unique_id', right_on='unique_id',
                                         how='left', indicator=True, suffixes=(
        '', '_x'))  # merging the total claim book and db claim book with total claim book on left
    drop_x(joined_df)  # droping the merged values to keep only orginal values

    new_claimbook_df = joined_df[joined_df[
                                     '_merge'] == 'left_only']  # Splitting the new claim book which is on the left only portion of the joined dataframe

    new_claimbook_df = new_claimbook_df.loc[:, new_claimbook_df.columns != '_merge']  # removing the merge indicator

    existing_claimbook_df = joined_df[joined_df[
                                          '_merge'] == 'both']  # Splitting the existing claim book records which is on the both portion of the joined dataframe

    existing_claimbook_df = existing_claimbook_df.loc[:,
                            existing_claimbook_df.columns != '_merge']  # removing the merge indicator

    # call the hash function to create a sum up string value in a new colum called hashstr
    hashing_job(existing_claimbook_df)
    hashing_job(existing_claimbook_in_db)

    overall_merge_of_existing_df = pd.merge(existing_claimbook_df, existing_claimbook_in_db, on='hash_str', how='left',
                                            indicator=True, suffixes=(
        '', '_x'))  # merging the existing claim book and db claim book with existing claim book on left
    drop_x(overall_merge_of_existing_df)  # droping the merged values to keep only orginal values

    updated_df = overall_merge_of_existing_df[overall_merge_of_existing_df[
                                                  '_merge'] == 'left_only']  # Splitting the claim book records that need to be updated which is on the left portion of the joined dataframe
    updated_df.drop(['_merge', 'hash_str'], axis=1, inplace=True)  # dropping the column we created

    # convert the dataframe to excel and save it in particular directory
    return updated_df, new_claimbook_df


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
        updated_df, new_claimbook_df = splitter(formatted_utr)
        file_name=every_list.upload.split("/")[-1]
        if updated_df.empty==True:
            write_file_insert_record(new_claimbook_df,f"new_{file_name}",every_list.name,upload_type="New")
        elif new_claimbook_df.empty==True:
            write_file_insert_record(updated_df,f"update_{file_name}",every_list.name,upload_type="Update")
        else:
            write_file_insert_record(updated_df,f"update_{file_name}",every_list.name,upload_type="Update")
            write_file_insert_record(new_claimbook_df,f"new_{file_name}",every_list.name,upload_type="New")
    
    return "Success"


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
        "document_type": doc.document_type,
        "status": "In Process",
        "file_url": file_url,
        "upload_type":upload_type,
    })
    doc.save(ignore_permissions=True)
    doc.reload()
    