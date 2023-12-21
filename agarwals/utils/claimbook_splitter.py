import pandas as pd

# addind up all he strings
def hashing_job(df_to_be_hashed):
        columns_to_be_hashed = ['Hospital','preauth_claim_id','mrn','doctor','department','case_id','first_name','tpa_name','insurance_company_name','tpa_member_id','insurance_policy_number','is_bulk_closure','al_number','cl_number','doa','dod','room_type','final_bill_number','final_bill_date','final_bill_amount','claim_amount','current_request_type','current_workflow_state','current_state_time','claim_submitted_date','reconcilled_status','utr_number','paid_on_date','requested_amount','approved_amount','provisional_bill_amount','settled_amount','patientpayable','patient_paid','tds_amount','tpa_shortfall_amount','forwarded_to_claims_date','courier_vendor','tracking_number','sent_date','recceived_date','preauth_submitted_date_time','is_admitted','visit_type','case_closed_in_preauth','unique_id','sub_date','Remarks','File Size']
        df_to_be_hashed['hash_str']= ""    # initializing the column Hash_str 
        if columns_to_be_hashed is not None:  
            for column in columns_to_be_hashed: # itrating throgh columns
                df_to_be_hashed['hash_str'] = df_to_be_hashed['hash_str'].astype(str) + df_to_be_hashed[column].astype(str)   # add the string value

# drop ing the merged column 
def drop_x(df):
    # list comprehension of the cols that end with '_x'
    to_drop = [x for x in df if x.endswith('_x')]
    df.drop(to_drop, axis=1, inplace=True)

# defining the path of the input and out put
TOTAL_CLAIMBOOK = 'C:/PROJECT/Agarwals/Claimbook/claimbook_sample.xlsx'
EXISTING_CLAIMBOOK_IN_DB = 'C:/PROJECT/Agarwals/Claimbook/Claimbook_db_sample.xlsx'
NEW_CLAIMBOOK = 'C:/PROJECT/Agarwals/Claimbook/output/new_claimbook.xlsx'
UPDATED_CLAIMBOOK = 'C:/PROJECT/Agarwals/Claimbook/output/updated_claimbook_sample.xlsx'

# reading inut as data frame
total_claimbook_df = pd.read_excel(TOTAL_CLAIMBOOK) 
existing_claimbook_in_db = pd.read_excel(EXISTING_CLAIMBOOK_IN_DB) 


joined_df = total_claimbook_df.merge(existing_claimbook_in_db,left_on='unique_id',right_on='unique_id',how='left',indicator=True,suffixes=('', '_x')) # merging the total claim book and db claim book with total claim book on left
drop_x(joined_df) # droping the merged values to keep only orginal values

new_claimbook_df = joined_df[joined_df['_merge'] == 'left_only'] # Splitting the new claim book which is on the left only portion of the joined dataframe
 
new_claimbook_df = new_claimbook_df.loc[:,new_claimbook_df.columns != '_merge'] # removing the merge indicator

existing_claimbook_df = joined_df[joined_df['_merge'] == 'both']    # Splitting the existing claim book records which is on the both portion of the joined dataframe

existing_claimbook_df = existing_claimbook_df.loc[:,existing_claimbook_df.columns != '_merge']   # removing the merge indicator

# call the hash function to create a sum up string value in a new colum called hashstr 
hashing_job(existing_claimbook_df) 
hashing_job(existing_claimbook_in_db)


overall_merge_of_existing_df = pd.merge(existing_claimbook_df,existing_claimbook_in_db,on='hash_str',how='left', indicator=True, suffixes=('', '_x'))       # merging the existing claim book and db claim book with existing claim book on left
drop_x(overall_merge_of_existing_df)# droping the merged values to keep only orginal values

updated_df = overall_merge_of_existing_df[overall_merge_of_existing_df['_merge']=='left_only'] # Splitting the claim book records that need to be updated which is on the left portion of the joined dataframe
updated_df.drop(['_merge','hash_str'], axis=1, inplace=True) # dropping the column we created


# convert the dataframe to excel and save it in particular directory 
updated_df.to_excel(UPDATED_CLAIMBOOK, index=False)           
new_claimbook_df.to_excel(NEW_CLAIMBOOK, index = False)