import pandas as pd
import os
import shutil
from agarwals.utils.path_data import SITE_PATH
import frappe
import openpyxl
from datetime import date

FOLDER_TRANSFORM = "Home/DrAgarwals/Transform"
IS_PRIVATE = 0


class Transformer():
    def __init__(self):
        self.file_type = ''
        self.document_type = ''
        self.source_df = pd.DataFrame()
        self.new_records = pd.DataFrame()
        self.modified_records = pd.DataFrame()
        self.unmodified_records = pd.DataFrame()

    def get_files_to_transform(self):
        file_query = f"""SELECT 
                            upload,name 
                        FROM 
                            `tabFile upload` 
                        WHERE 
                            status = 'Open' AND document_type = '{self.file_type}'"""
        files = frappe.db.sql(file_query, as_dict=True)
        return files

    def get_columns_to_be_queried(self):
        return []

    def get_target_df(self):
        return []

    def get_join_columns(self):
        self.left_df_column = ''
        self.right_df_column = ''
        return self.left_df_column, self.right_df_column

    def left_join(self, left_df, right_df):
        left_on, right_on = self.get_join_columns()
        merged_df = left_df.merge(right_df, left_on=left_on, right_on=right_on, how='left', indicator=True,
                                  suffixes=('', '_x'))
        return merged_df

    def prune_columns(self, df):
        columns_to_prune = self.get_columns_to_prune()
        for column in columns_to_prune:
            df = df.loc[:df.columns != column]
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

    def write_excel(self, df, file_path, type):
        file_path = file_path.replace('extract', 'transform').replace('.csv', '.xlsx').replace('.xlsx','_' + type + '.xlsx')
        file_path_to_write = SITE_PATH + file_path
        df.to_excel(file_path_to_write, index=False)
        return file_path

    def create_file_record(self, file_url):
        file_name = file_url.split('/')[-1]
        file = frappe.new_doc('File')
        file.set('file_name', file_name)
        file.set('is_private', IS_PRIVATE)
        file.set('folder', FOLDER_TRANSFORM)
        file.set('file_url', file_url)
        file.save(ignore_permissions=True)

    def insert_in_file_upload(self, file_url, file_upload_name, type):
        file_upload = frappe.get_doc('File upload', file_upload_name)
        file_upload.append('transform',
                           {
                               'date': date.today(),
                               'document_type': self.document_type,
                               'type': type,
                               'file_url': file_url,
                               'status': 'Open'
                           })
        file_upload.save(ignore_permissions=True)

    def move_to_transform(self, file, df, type):
        if df.empty:
            return None

        df = self.prune_columns(df)
        file_path = self.write_excel(df, file['upload'], type)
        self.create_file_record(file_path)
        self.insert_in_file_upload(file_path, file['name'], type)

    def read_file(self, file):
        if file['upload'].endswith('.xls') or file['upload'].endswith('.xlsx'):
            self.source_df = pd.read_excel(SITE_PATH + file['upload'], engine='openpyxl')
        elif file['upload'].endswith('.csv'):
            self.source_df = pd.read_csv(SITE_PATH + file['upload'])
        else:
            self.log_error(self.document_type, file['name'], 'The File should be XLSX or CSV')

    def process(self):
        files = self.get_files_to_transform()
        for file in files:
            self.read_file(file)
            if self.source_df.empty:
                self.log_error(self.document_type, file['name'], 'The File was Empty')
                continue

            target_df = self.get_target_df()
            merged_df = self.left_join(self.source_df, target_df)
            self.new_records = merged_df[merged_df['_merge'] == 'left_only']
            existing_df = merged_df[merged_df['_merge'] == 'both']
            self.modified_records, self.unmodified_records = self.split_modified_and_unmodified_records(existing_df)
            self.move_to_transform(file, self.new_records, 'insert')
            self.move_to_transform(file, self.modified_records, 'update')
            self.move_to_transform(file, self.unmodified_records, 'skip')


class BillTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Debtor Report'
        self.document_type = 'Bill'

    def get_target_df(self):
        query = f"""
                     SELECT 
                         name, status
                     FROM 
                         `tab{self.document_type}`
                     """
        records = frappe.db.sql(query, as_dict=True)
        records = pd.DataFrame(records)
        return records

    def get_join_columns(self):
        self.left_df_column = 'Bill No'
        self.right_df_column = 'name'
        return self.left_df_column, self.right_df_column

    def get_columns_to_prune(self):
        return ['name', '_merge', 'status_x']

    def get_columns_to_check(self):
        return {'status': 'status_x'}


class ClaimbookTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Claim Book'
        self.document_type = 'ClaimBook'
