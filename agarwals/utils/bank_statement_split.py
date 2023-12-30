import pandas as pd
import os
import shutil

ROOT_PATH = "D:\\work\\projects\\Agarwals\\Q3\\prs-conversion-tools\\source"
TN_PATH = "D:\\work\\projects\\Agarwals\\Q3\\FILES - TFS - 27.11.2023\\Bank Statements\\TN"
ROTN_PATH = "D:\\work\\projects\\Agarwals\\Q3\\FILES - TFS - 27.11.2023\\Bank Statements\\ROTN"

def separate_sheets(region, input_excel, output_folder):
    xls = pd.ExcelFile(input_excel)
    
    if region == 'TN':
        month = input_excel.split('--')[-1].replace('.xls', '')
    else:
        month = input_excel.split('-')[-1].replace('.xlsx', '')

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name)
        df = df.replace('\n', ' ', regex=True)
        output_file = f"{output_folder}/{region}-{sheet_name}-{month}.csv"
        df.to_csv(output_file, index=False)
 
        print(f"Sheet '{sheet_name}' processed")

def process_files(region, path):
    for root, dirs, files in os.walk(path):
        for file in files:
            input_excel_path = os.path.join(root, file)
            separate_sheets(region, input_excel_path, ROOT_PATH)

def main():
    if len(os.listdir(ROOT_PATH)) != 0:
        for file in os.listdir(ROOT_PATH):
            os.remove(ROOT_PATH +"\\" + file)

    process_files('TN', TN_PATH)
    process_files('ROTN', ROTN_PATH)

if __name__ == "__main__":
    main()