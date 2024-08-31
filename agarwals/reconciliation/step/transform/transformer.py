import os
import json
import pandas as pd
import frappe
from datetime import date
import hashlib
from agarwals.utils.loader import Loader
from tfs.orchestration import update_chunk_status
from agarwals.utils.error_handler import log_error as error_handler

control_panel = frappe.get_single('Control Panel')
SITE_PATH = control_panel.site_path
FOLDER = f'Home/{control_panel.project_folder}'
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
        self.is_truncate_excess_char = False
        self.max_trim_length = 140
        self.loading_configuration = None
        self.skip_invalid_rows_in_csv = False

    def get_file_columns(self):
        return self.loading_configuration.columns_to_get_from_file

    def get_files_to_transform(self):
        fields = self.get_file_columns()
        file_query = f"""SELECT 
                            {fields} 
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
        left_df_column = json.loads(self.loading_configuration.column_to_join.replace("'", '"'))["left"]
        right_df_column = json.loads(self.loading_configuration.column_to_join.replace("'", '"'))["right"]
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
            columns_to_prune = []
            columns = self.get_columns_to_prune()
            for column in columns:
                if column in df.columns:
                    columns_to_prune.append(column)
        unnamed_columns = [self.trim_and_lower(column) for column in df.columns if 'unnamed' in column or 'nan' in column]
        if unnamed_columns:
            columns_to_prune.extend(unnamed_columns)
        df = df.drop(columns=columns_to_prune, errors='ignore')
        return df

    def get_columns_to_prune(self):
        return eval(self.loading_configuration.column_to_prune)

    def get_columns_to_check(self):
        return eval(self.loading_configuration.column_to_check_the_difference)

    def split_modified_and_unmodified_records(self, df):
        columns_to_check = self.get_columns_to_check()
        modified_records = pd.DataFrame()
        for left_column, right_column in columns_to_check.items():
            modified_records = pd.concat([modified_records, df[~(df[left_column] == df[right_column])]], axis=0)
            df = df[df[left_column] == df[right_column]]
        return modified_records, df

    def log_error(self, doctype_name, error_message , reference_name = None):
        error_handler(error=error_message, doc=doctype_name, doc_name=reference_name)

    def get_column_needed(self):
        return eval(self.loading_configuration.column_needed)

    def reorder_columns(self,column_orders,df):
        df = self.convert_into_common_format(df,column_orders)
        return df[column_orders]

    def write_excel(self, df, file_path, type, target_folder):
        column_orders = self.get_column_needed()
        if column_orders:
            df = self.reorder_columns(column_orders,df)
        excel_file_path = file_path.replace(file_path.split('.')[-1],'xlsx')
        file_path = excel_file_path.replace('Extract', target_folder).replace('.xlsx','_' + type + '.xlsx')
        file_path_to_write = SITE_PATH + file_path
        df.to_excel(file_path_to_write, index=False)
        return file_path

    def create_file_record(self, file_url,folder):
        file_name = file_url.split('/')[-1]
        file = frappe.new_doc('File')
        file.set('file_name', file_name)
        file.set('is_private', IS_PRIVATE)
        file.set('folder', os.path.join(FOLDER,folder))
        file.set('file_url', file_url)
        file.save()
        frappe.db.set_value('File',file.name,'file_url',file_url)

    def insert_in_file_upload(self, file_url, file_upload_name, type, status, transform_child):
        file_upload = frappe.get_doc('File upload', file_upload_name)
        transform_child.update({
            'type': type,
            'file_url': file_url,
            'status': status
        })
        file_upload.transform.append(transform_child)
        file_upload.save(ignore_permissions=True)

    def create_transform_record(self, file_upload_name):
        file_upload = frappe.get_doc('File upload', file_upload_name)
        transform = file_upload.append('transform',
                                       {
                                           'date': date.today(),
                                           'document_type': self.document_type,
                                       })
        file_upload.save(ignore_permissions=True)
        return transform

    def move_to_transform(self, file, df, type, folder, prune = True, status = 'Open'):
        if df.empty:
            return None
        if self.is_truncate_excess_char == True:
            df = df.applymap(lambda x:str(x)[:self.max_trim_length] if len(str(x)) > self.max_trim_length else x)
        if prune:
            df = self.prune_columns(df)
        if self.clean_utr == 1:
           df = self.format_utr(df ,self.utr_column_name)
        df = self.format_numbers(df)
        transform = self.create_transform_record(file['name'])
        df["file_upload"] = file['name']
        df["transform"] = transform.name
        file_path = self.write_excel(df, file['upload'], type,folder)
        self.create_file_record(file_path,folder)
        self.insert_in_file_upload(file_path, file['name'], type, status, transform)


    def load_source_df(self, file, header):
        try:
            if file['upload'].lower().endswith('.csv'):
                self.source_df = pd.read_csv(SITE_PATH + file['upload'], header=header , on_bad_lines='skip') if self.skip_invalid_rows_in_csv else pd.read_csv(SITE_PATH + file['upload'], header=header)
            else:
                 self.source_df = pd.read_excel(SITE_PATH + file['upload'], header=header)
            self.source_df["index"] = [i for i in range(2, len(self.source_df) + 2)]
        except Exception as e:
            self.log_error(doctype_name=self.document_type, reference_name=file['name'],error_message=e)
            self.update_status('File upload', file['name'], 'Error')

    def get_columns_to_hash(self):
        return eval(self.loading_configuration.column_to_hash)

    def hashing_job(self):
        self.source_df['hash_column'] = ''
        columns_to_hash = self.get_columns_to_hash()
        for column in columns_to_hash:
            self.source_df['hash_column'] = self.source_df['hash_column'].astype(str) + self.source_df[column].astype(str)
        self.source_df['hash'] = self.source_df['hash_column'].apply(lambda x: hashlib.sha1(x.encode('utf-8')).hexdigest())

    def update_status(self, doctype, name, status):
        if doctype == 'File upload':
            doc = frappe.get_doc('File upload',name)
            doc.status = status
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        else:
            frappe.db.set_value(doctype,name,'status',status)
            frappe.db.commit()

    def update_count(self, doctype, name):
        file_record = frappe.get_doc(doctype, name)
        file_record.total_records = len(self.source_df)
        file_record.insert_records = len(self.new_records)
        file_record.update_records = len(self.modified_records)
        file_record.skipped_records = len(self.unmodified_records)
        file_record.save(ignore_permissions=True)
        frappe.db.commit()

    def update_parent(self, file):
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
        self.update_count('File upload', file['name'])

    def remove_x_in_UTR(self, item):
        if "XXXXXXX" in str(item):
            return item.replace("XXXXXXX", '')
        elif "XX" in str(item) and len(item) > 16:
            return item.replace("XX", '')
        return item

    def format_utr(self,df,utr_column):
        utr_list = df[utr_column].fillna(0).to_list()
        new_utr_list = []
        for item in utr_list:
            item = str(item).replace('UIIC_', 'CITIN')
            item = str(item).replace('UIC_', 'CITIN')
            if str(item).startswith(('23','24','25','26','27','28','29','30')) and len(str(item)) == 11:
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
        df['final_utr_number'] = new_utr_list
        return df

    def transform(self, file):
        return None

    def trim_and_lower(self, word):
        return str(word).strip().lower().replace(' ', '')

    def validate_header(self, header_row, source_column_list):
        return 'Not Identified', 0, []

    def clean_header(self, list_to_clean):
        return None

    def find_and_validate_header(self, header_list, source_column_list):
        for header in header_list:
            header_row_index = None
            for index, row in self.source_df.iterrows():
                if self.trim_and_lower(header) in self.clean_header(row.values):
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
        return eval(self.loading_configuration.column_to_convert_the_values_to_numeric)

    def convert_column_to_numeric(self):
        columns = self.get_column_name_to_convert_to_numeric()
        for column in columns:
            if column in self.source_df.columns:
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
        return eval(self.loading_configuration.column_to_convert_na_to_0)

    def fill_na_as_0(self,df):
        columns = self.get_columns_to_fill_na_as_0()
        for column in columns:
            if column in df.columns:
                df[column] = df[column].fillna(0)
                df[column] = df[column].astype(str).apply(lambda x: 0 if x == '-' else x)
        return df

    def format_numbers(self, df):
        columns = self.get_column_name_to_convert_to_numeric()
        for column in columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column].astype(str).str.replace(r"[^0-9.-]", "", regex=True)).round(2)
        return df

    def extract(self):
        pass

    @update_chunk_status
    def process(self):
        status = "Processed"
        self.loading_configuration = frappe.get_doc("Data Loading Configuration", self.document_type)
        files = self.get_files_to_transform()
        if not files:
            return status
        for file in files:
            try:
                self.update_status('File upload', file['name'], 'In Process')
                self.load_source_df(file, self.header)
                if self.source_df.empty:
                    self.log_error(self.document_type, file['name'], 'The File is Empty')
                    self.update_status('File upload', file['name'], 'Error')
                    status = "Error"
                    continue
                transformed = self.transform(file)
                if not transformed:
                    continue
            except Exception as e:
                self.log_error(self.document_type, file['name'], e)
                self.update_status('File upload', file['name'], 'Error')
                status = "Error"
                continue
            loader = Loader(self.document_type)
            loader.process()
            self.update_parent(file)
        return status

