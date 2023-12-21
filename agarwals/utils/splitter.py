import os.path

import pandas as pd

import frappe
import hashlib


@frappe.whitelist()
def splitter(input_file, document_type):
    output_dir = os.path.split(input_file)[0]
    file_name_with_ext = os.path.split(input_file)[1]
    file_name = file_name_with_ext.split('.')[0]

    print("Hello 1")

    match document_type:
        case 'Bill':
            left_on = 'Bill No'
        case 'ClaimBook':
            left_on = 'unique_id'
        case _:
            return "No Document Type Found"
    left_df = pd.read_excel(input_file)
    right_df = pd.DataFrame(frappe.get_list('Bill',pluck = 'name'),columns=['name'])


    joined_df = left_df.merge(right_df, left_on = left_on, right_on = 'name',how = 'left', indicator=True)

    if document_type == "Bill":
        joined_df['Branch'] = joined_df['Branch'].astype(str) + ' - A'

    column_array = joined_df.columns.values

    joined_df['column_to_be_hashed'] = ''

    for column in column_array:
        joined_df['column_to_be_hashed'] = joined_df['column_to_be_hashed'].astype(str) + joined_df[column].astype(str)


    joined_df['hashed_value'] = joined_df['column_to_be_hashed'].apply(lambda x: hashlib.sha1(x.encode('utf-8')).hexdigest())

    new_df = joined_df[joined_df['_merge'] == 'left_only']
    new_df = new_df.loc[:,new_df.columns != '_merge']
    new_df = new_df.loc[:,new_df.columns != 'name']

    new_df.to_excel(output_dir+'/'+file_name+'_new.xlsx',index = False)

    existing_df = joined_df[joined_df['_merge'] == 'both']
    existing_df = existing_df.loc[:,existing_df.columns != '_merge']

    existing_df.to_excel(output_dir+'/'+file_name+'_update.xlsx', index = False)



