import pandas as pd
from agarwals.utils.path_data import SITE_PATH
import frappe
from datetime import date
import hashlib
import re
import json
from agarwals.utils.loader import Loader

FOLDER = "Home/DrAgarwals/"
IS_PRIVATE = 1

class Transformer:
    def __init__(self):
        self.file_type = ''
        self.document_type = ''
        self.source_df = pd.DataFrame()
        self.target_df = pd.DataFrame()
        self.new_records = pd.DataFrame()
        self.modified_records = pd.DataFrame()
        self.unmodified_records = pd.DataFrame()
        self.file = ''
        self.hashing = 0
        self.clean_utr = 0
        self.utr_column_name = ''
        self.header = 0

    def get_files_to_transform(self):
        file_query = f"""SELECT 
                            upload,name 
                        FROM 
                            `tabFile upload` 
                        WHERE 
                            status = 'Open' AND document_type = '{self.file_type}'
                            ORDER BY creation"""
        files = frappe.db.sql(file_query, as_dict=True)
        return files

    def get_columns_to_be_queried(self):
        return []

    def load_target_df(self):
        return []

    def get_join_columns(self):
        left_df_column = ''
        right_df_column = ''
        return left_df_column, right_df_column

    def left_join(self,file):
        try:
            left_on, right_on = self.get_join_columns()
            merged_df = self.source_df.merge(self.target_df, left_on=left_on, right_on=right_on, how='left',
                                             indicator=True,
                                             suffixes=('', '_x'))
            return merged_df

        except Exception as e:
            self.update_status('File upload', file['name'], 'Error')
            self.log_error('File upload',file['name'],e)
            return pd.DataFrame()

    def prune_columns(self, df, columns_to_prune = None):
        if columns_to_prune is None:
            columns_to_prune = self.get_columns_to_prune()
        df = df.drop(columns=columns_to_prune, errors='ignore')
        return df

    def get_columns_to_prune(self):
        return []

    def get_columns_to_check(self):
        return {}

    def split_modified_and_unmodified_records(self, df):
        columns_to_check = self.get_columns_to_check()
        modified_records = pd.DataFrame()
        for left_column, right_column in columns_to_check.items():
            modified_records = pd.concat([modified_records, df[~(df[left_column] == df[right_column])]], axis=0)
            df = df[df[left_column] == df[right_column]]
        return modified_records, df

    def log_error(self, doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()

    def get_column_needed(self):
        return []

    def reorder_columns(self,column_orders,df):
        return df[column_orders]

    def write_excel(self, df, file_path, type, target_folder):
        column_orders = self.get_column_needed()
        if column_orders:
            df = self.reorder_columns(column_orders,df)
        file_path = file_path.replace('Extract', target_folder).replace('.csv', '.xlsx').replace('.xlsx','_' + type + '.xlsx')
        file_path_to_write = SITE_PATH + file_path
        df.to_excel(file_path_to_write, index=False)
        return file_path

    def create_file_record(self, file_url,folder):
        file_name = file_url.split('/')[-1]
        file = frappe.new_doc('File')
        file.set('file_name', file_name)
        file.set('is_private', IS_PRIVATE)
        file.set('folder', FOLDER + folder)
        file.set('file_url', file_url)
        file.save()
        frappe.db.set_value('File',file.name,'file_url',file_url)

    def insert_in_file_upload(self, file_url, file_upload_name, type, status):
        file_upload = frappe.get_doc('File upload', file_upload_name)
        file_upload.append('transform',
                           {
                               'date': date.today(),
                               'document_type': self.document_type,
                               'type': type,
                               'file_url': file_url,
                               'status': status
                           })
        file_upload.save(ignore_permissions=True)

    def move_to_transform(self, file, df, type, folder, prune = True, status = 'Open'):
        if df.empty:
            return None
        if prune:
            df = self.prune_columns(df)
        if self.clean_utr == 1:
            self.format_utr(self.utr_column_name)
        file_path = self.write_excel(df, file['upload'], type,folder)
        self.create_file_record(file_path,folder)
        self.insert_in_file_upload(file_path, file['name'], type, status)

    def load_source_df(self, file, header):
        try:
            if file['upload'].endswith('.xls') or file['upload'].endswith('.xlsx'):
                self.source_df = pd.read_excel(SITE_PATH + file['upload'], engine='openpyxl', header=header)
            elif file['upload'].endswith('.csv'):
                self.source_df = pd.read_csv(SITE_PATH + file['upload'], header=header)
            else:
                self.log_error(self.document_type, file['name'], 'The File should be XLSX or CSV')
                self.update_status('File upload', file['name'], 'Error')
        except Exception as e:
            self.log_error(self.document_type, file['name'], e)
            self.update_status('File upload', file['name'], 'Error')

    def get_columns_to_hash(self):
        return []

    def hashing_job(self):
        self.source_df['hash_column'] = ''
        columns_to_hash = self.get_columns_to_hash()
        for column in columns_to_hash:
            self.source_df['hash_column'] = self.source_df['hash_column'].astype(str) + self.source_df[column].astype(str)
        self.source_df['hash'] = self.source_df['hash_column'].apply(lambda x: hashlib.sha1(x.encode('utf-8')).hexdigest())

    def update_status(self, doctype, name, status):
        frappe.db.set_value(doctype,name,'status',status)
        frappe.db.commit()

    def update_parent_status(self,file):
        file_record = frappe.get_doc('File upload',file['name'])
        transform_records = file_record.transform
        transform_record_status = []
        for transform_record in transform_records:
            transform_record_status.append(transform_record.status)
        if "Error" in transform_record_status:
            self.update_status('File upload',file['name'],'Error')
        elif "Partial Success" in transform_record_status:
            self.update_status('File upload', file['name'], 'Partial Success')
        else:
            self.update_status('File upload', file['name'], 'Success')

    def remove_x_in_UTR(self, item):
        if "XXXXXXX" in str(item):
            return item.replace("XXXXXXX", '')
        elif "XX" in str(item) and len(item) > 16:
            return item.replace("XX", '')
        return item

    def format_utr(self,utr_column):
        utr_list = self.source_df[utr_column].fillna(0).to_list()
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
                    new_utr_list.append(self.remove_x_in_UTR(item))
            elif '-' in str(item):
                item = item.split('-')
                new_utr_list.append(self.remove_x_in_UTR(item[-1]))
            else:
                new_utr_list.append(self.remove_x_in_UTR(item))

        self.source_df['final_utr_number'] = new_utr_list

    def transform(self, file):
        return None

    def trim_and_lower(self, word):
        return str(word).strip().lower().replace(' ', '')

    def validate_header(self, header_row, source_column_list):
        return 'Not Identified', 0, []

    def find_and_validate_header(self, header_list, source_column_list):
        for header in header_list:
            header_row_index = None
            for index, row in self.source_df.iterrows():
                if header in row.values:
                    header_row_index = index
                    break
            if header_row_index is not None:
                key, header_row_index, identified_header_row = self.validate_header(header_row_index,source_column_list)
                return key, header_row_index, identified_header_row
        return 'Not Identified', 0, []

    def rename_columns(self,df,columns):
        df = df.rename(columns=columns)
        df = df.loc[:, ~self.source_df.columns.duplicated()]
        return df

    def convert_into_common_format(self,df,columns_to_select):
        columns = []
        for column in columns_to_select:
            if column in df.columns:
                columns.append(column)
            else:
                df[column] = ''
        return df

    def get_column_name_to_convert_to_numeric(self):
        return []

    def convert_column_to_numeric(self):
        columns = self.get_column_name_to_convert_to_numeric()
        for column in columns:
            self.source_df[column] = pd.to_numeric(self.source_df[column], errors='coerce')

    def format_date(self,df,date_formats,date_column):
        df['original_date'] = df[date_column].astype(str).apply(lambda x: x.strip() if isinstance(x,str) else x)
        df['formatted_date'] = pd.NaT
        for fmt in date_formats:
            new_column = 'date_' + fmt.replace('%','').replace('/','_').replace(':','').replace(' ','_')
            df[new_column] = pd.to_datetime(df['original_date'],format = fmt, errors='coerce')
            df['formatted_date'] = df['formatted_date'].combine_first(df[new_column])
        df[date_column] = df['formatted_date']
        df = self.prune_columns(df,[col for col in df.columns if 'date_' in col or col == 'formatted_date' or col == 'original_date'])
        return df

    def get_columns_to_fill_na_as_0(self):
        return []

    def fill_na_as_0(self,df):
        columns = self.get_columns_to_fill_na_as_0()
        for column in columns:
            df[column] = df[column].fillna(0)
            df[column] = df[column].astype(str).apply(lambda x: 0 if x == '-' else x)
        return df

    def process(self):
        files = self.get_files_to_transform()
        if not files:
            return None
        for file in files:
            self.update_status('File upload', file['name'], 'In Process')
            self.load_source_df(file,self.header)

            try:
                if self.source_df.empty:
                    self.log_error(self.document_type, file['name'], 'The File is Empty')
                    self.update_status('File upload', file['name'], 'Error')
                    continue
                transformed =self.transform(file)
                if not transformed:
                    continue
                self.move_to_transform(file, self.new_records, 'Insert', 'Transform', True)

            except Exception as e:
                self.log_error(self.document_type, file['name'], e)
                self.update_status('File upload', file['name'], 'Error')
                continue
            loader = Loader(self.document_type)
            loader.process()
            self.update_parent_status(file)

class DirectTransformer(Transformer):
    def __init__(self):
        super().__init__()

    def transform(self, file):
        if self.hashing == 1:
            self.hashing_job()

        self.load_target_df()

        if self.target_df.empty:
            self.new_records = self.source_df
            self.move_to_transform(file, self.new_records, 'Insert', 'Transform', False)
        else:
            merged_df = self.left_join(file)
            if merged_df.empty:
                return False
            self.new_records = merged_df[merged_df['_merge'] == 'left_only']
            existing_df = merged_df[merged_df['_merge'] == 'both']
            self.modified_records, self.unmodified_records = self.split_modified_and_unmodified_records(
                existing_df)
            self.move_to_transform(file, self.modified_records, 'Update', 'Transform', True)
            self.move_to_transform(file, self.unmodified_records, 'Skip', 'Bin', True, 'Skipped')

class BillTransformer(DirectTransformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Debtors Report'
        self.document_type = 'Bill'

    def load_target_df(self):
        query = f"""
                     SELECT 
                         name, status
                     FROM 
                         `tab{self.document_type}`
                     """
        records = frappe.db.sql(query, as_list=True)
        self.target_df = pd.DataFrame(records,columns = ['name','status'])

    def get_join_columns(self):
        left_df_column = 'Bill No'
        right_df_column = 'name'
        return left_df_column, right_df_column

    def get_columns_to_prune(self):
        return ['name', '_merge', 'status']

    def get_columns_to_check(self):
        return {'Status': 'status'}

    def get_column_needed(self):
        return []
class ClaimbookTransformer(DirectTransformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Claim Book'
        self.document_type = 'ClaimBook'
        self.hashing = 1
        self.clean_utr = 1

    def get_columns_to_hash(self):
        return ['unique_id', 'settled_amount']

    def load_target_df(self):
        query = f"""
                      SELECT 
                          name, hash
                      FROM 
                          `tab{self.document_type}`
                      """
        records = frappe.db.sql(query, as_list=True)
        self.target_df = pd.DataFrame(records, columns=['name', 'hash'])

    def get_join_columns(self):
        left_df_column = 'unique_id'
        right_df_column = 'name'
        return left_df_column, right_df_column

    def get_columns_to_prune(self):
        return ['name', '_merge', 'hash_x', 'hash_column']

    def get_columns_to_check(self):
        return {'hash': 'hash_x'}

    def get_column_needed(self):
        return []

class StagingTransformer(Transformer):
    def __init__(self):
        super().__init__()


    def get_configuration(self):
        return []

    def get_header_identification_keys(self, configuration):
        return []

    def get_source_column_dict(self, configuration):
        return {}

    def verify_file(self,file,header_index):
        return

    def extract(self,configuration,key,bank):
        return

    def extract_transactions(self, column):
        null_index = self.source_df.index[self.source_df[column].isnull()].min()
        self.source_df = self.source_df.loc[:null_index - 1]


    def transform(self,file):
        configuration = self.get_configuration()
        header_identification_keys = self.get_header_identification_keys(configuration)
        source_column_dict = self.get_source_column_dict(configuration)
        key, header_index, cleaned_header_row = self.find_and_validate_header(header_identification_keys,source_column_dict)

        if key == 'Not Identified':
            self.log_error(self.document_type, file['name'], 'Unable to Identify the Header row')
            self.update_status('File upload', file['name'], 'Error')
            return False

        valid = self.verify_file(file,header_index)
        if not valid:
            return False

        self.load_source_df(file, header_index)
        self.source_df.columns = [self.trim_and_lower(column) for column in self.source_df.columns]
        self.prune_columns(self.source_df)
        self.source_df.columns = cleaned_header_row
        self.extract(configuration,key,file)
        self.source_df = self.fill_na_as_0(self.source_df)
        self.new_records = self.source_df
        return True


class BankTransformer(StagingTransformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Bank Statement'
        self.document_type = 'Bank Transaction Staging'
        self.header = None

    def get_files_to_transform(self):
        file_query = f"""SELECT 
                            upload,name,date,bank_account 
                        FROM 
                            `tabFile upload` 
                        WHERE 
                            status = 'Open' AND document_type = '{self.file_type}'
                            ORDER BY creation"""
        files = frappe.db.sql(file_query, as_dict=True)
        return files

    def validate_header(self, header_row_index, source_column_list):
        identified_header_row = [self.trim_and_lower(column) for column in
                                 self.source_df.loc[header_row_index].to_list() if
                                 'nan' not in str(column) and str(column) != '*' and str(column) != '.']
        for key, columns in source_column_list.items():
            columns = [self.trim_and_lower(column) for column in columns]
            if set(identified_header_row) == set(columns):
                return key, header_row_index, identified_header_row
        return 'Not Identified', 0, []

    def verify_file(self,file,header_index):
        valid = False
        bank_account = file['bank_account'].split('-')[-2].strip()
        df = self.source_df.loc[:header_index]
        for index, row in df.iterrows():
            if any(bank_account in str(value) for value in row.values):
                valid = True
        if not valid:
            self.log_error(self.document_type, file['name'], 'Wrong Bank Account Statement Uploaded')
            self.update_status('File upload', file['name'], 'Error')
        return valid

    def get_column_needed(self):
        return ['date','narration','utr_number','credit','debit','search','source','bank_account','reference_number']

    def get_configuration(self):
        return frappe.get_single('Bank Configuration')

    def add_search_column(self):
        self.source_df['search'] = self.source_df['narration'].str.replace(r'[\'"\s]', '', regex=True).str.lower()

    def get_column_name_to_convert_to_numeric(self):
        return ['credit','debit']


    def utr_validation(self, pattern, token):
        return bool(re.match(pattern, token))

    def extract_utr_by_length(self,narration, length, delimiters, pattern):
        if len(narration) < length:
            return None

        for delimiter in delimiters:
            for token in map(str.strip, narration.split(delimiter)):
                if len(token) == length and len(token.strip()) == length:
                    if self.utr_validation(pattern, token):
                        return token

        return None

    def extract_utr(self, narration, reference, delimiters):
        numeric = '^[0-9]+$'
        alphanumeric_pattern = '^[a-zA-Z]*[0-9]+[a-zA-Z0-9]*$'
        if "IMPS" in narration:
            length = 12
            pattern = numeric
        elif "NEFT" in narration:
            pattern = alphanumeric_pattern
            utr_13 = None
            utr_16 = None
            if "CMS" in narration:
                utr_13 = self.extract_utr_by_length(narration, 13, delimiters, pattern)
            utr_16 = self.extract_utr_by_length(narration, 16, delimiters, pattern)
            return utr_13 or utr_16 or reference
        elif "RTGS" in narration:
            length = 22
            pattern = alphanumeric_pattern
        elif "IFT" in narration:
            length = 12
            pattern = alphanumeric_pattern
        elif "UPI" in narration:
            length = 12
            pattern = numeric
        else:
            return reference

        return self.extract_utr_by_length(narration, length, delimiters, pattern) or reference

    def extract_utr_from_narration(self, configuration):
        self.source_df['reference_number'] = self.source_df.apply(lambda row: self.extract_utr(row['narration'], row['utr_number'],eval(configuration.delimiters)), axis = 1)

    def add_source_and_bank_account_column(self, source, bank_account):
        self.source_df['source'] = source
        self.source_df['bank_account'] = bank_account

    def get_columns_to_fill_na_as_0(self):
        return ['reference_number']

    def get_header_identification_keys(self,configuration):
        return eval(configuration.types_of_narration_column)

    def get_source_column_dict(self,configuration):
        return json.loads(configuration.bank_and_source_columns.replace("'", '"'))

    def extract(self,configuration,key,file):
        self.source_df = self.rename_columns(self.source_df,json.loads(configuration.bank_and_target_columns.replace("'", '"'))[key])
        if key in eval(configuration.first_row_empty):
            self.source_df = self.source_df[1:]
        self.extract_transactions("narration")
        if key in eval(configuration.skip_row_1):
            self.source_df = self.source_df.loc[1:]
        if key in eval(configuration.banks_having_crdr_column):
            self.source_df['credit'] = self.source_df['amount'].where(self.source_df['cr/dr'].str.lower() == 'cr')
            self.source_df['debit'] = self.source_df['amount'].where(self.source_df['cr/dr'].str.lower() == 'dr')
        columns_to_select = self.get_column_needed()
        self.source_df = self.convert_into_common_format(self.source_df,columns_to_select)
        self.add_search_column()
        self.convert_column_to_numeric()
        self.extract_utr_from_narration(configuration)
        self.add_source_and_bank_account_column(file['name'], file['bank_account'])
        self.source_df = self.format_date(self.source_df,eval(configuration.date_formats),'date')