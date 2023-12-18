import os.path

import pandas as pd
import numpy as np

import frappe


@frappe.whitelist()
def splitter(input_file, document_type):
    output_dir = os.path.split(input_file)[0]
    file_name = os.path.split(input_file)[1]

    print("Hello 1")

    match document_type:
        case 'Bill':
            left_on = 'Bill No'
        case 'ClaimBook':
            left_on = 'unique_id'
        case _:
            return "No Document Type Found"
    left_df = pd.read_excel(input_file)
    right_df = np.array(frappe.get_list(document_type,pluck='name'))

    joined_df = left_df.merge(right_df, left_on = left_on, right_on = 'name',how = 'left', indicator=True)

    new_df = joined_df[joined_df['merge'] == 'left_only']
    new_df = new_df.loc[:,new_df != '_merge']
    new_df = new_df.loc[:,new_df != 'name']

    new_df.to_excel(output_dir+'new'+file_name,index = False)

    existing_df = joined_df[joined_df['merge'] == 'both']
    existing_df = existing_df.loc[:,existing_df != '_merge']
    existing_df = existing_df.loc[:,existing_df != left_on]

    existing_df.to_excel(output_dir+'existing'+file_name, index = False)

