import pandas as pd
import os
import json
# defining the path of the input and out put
folder = 'C:/PROJECT/Agarwals/SettlementAdvice/'
target_folder = 'C:/PROJECT/Agarwals/sa-import/total_mediassist.xlsx'

def advice_transform():
    json={"Mediassist India Tpa P Ltd":{"Claim Number": "claim_id", 
                                    "Claimed Amount": "claimed_amount",
                                    "Cheque/ NEFT/ UTR No.":"utr_number",
                                    "Settled Amount":"settled_amount",
                                    "TDS Amount":"tds_amount","Claim Status":"claim_status"},}

    clm_vlaues=json["Mediassist India Tpa P Ltd"]


    # Get the list of all files and directories
    dir_list = os.listdir(folder)
    
    print("Files and directories in '", folder, "' :")
    
    # prints all files
    # print(dir_list)
    total_df=pd.DataFrame()
    for file in dir_list:
        # print("File:", file)
        df = pd.read_excel(folder + file)
        # print(df.columns)
        df=df.rename(columns=clm_vlaues)
        df = df[df["claim_status"] == "Settled"]
        df = df[['claim_id', 'claimed_amount', 'utr_number', 'settled_amount', 'tds_amount']]
        
        total_df=pd.concat([total_df,df],axis=0)


    total_df=total_df.rename(columns=json)
    print(total_df)
    format_utr(total_df)

    # total_df.to_excel(target_folder,index=False)

    # print(total_df)
    print(sum(total_df['settled_amount']))
        
    print(len(total_df))
    #total_claimbook_df = pd.read_excel(TOTAL_CLAIMBOOK) 
    #existing_claimbook_in_db = pd.read_excel(EXISTING_CLAIMBOOK_IN_DB) 


def remove_x(item):
    if "XXXXXXX" in str(item):
        return item.replace("XXXXXXX",'')
    elif "XX" in str(item) and len(item) > 16:
        return item.replace("XX",'')
    return item

def format_utr(df):
    utr_list = df.fillna(0).utr_number.to_list()
    new_utr_list = []
    
    for item in utr_list:
            item = str(item).replace('UIIC_','CITIN')
            item = str(item).replace('UIC_','CITIN')
    
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

