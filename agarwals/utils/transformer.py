import pandas as pd
import os
import shutil
from agarwals.utils.path_data import SITE_PATH
import frappe
import openpyxl
from datetime import date
import hashlib
from agarwals.utils.loader import Loader

FOLDER = "Home/DrAgarwals/"
IS_PRIVATE = 1


class Transformer():
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
            self.change_status('File upload', file['name'], 'Error')
            self.log_error('File upload',file['name'],e)

    def prune_columns(self, df):
        columns_to_prune = self.get_columns_to_prune()
        for column in columns_to_prune:
            df = df.loc[:,df.columns != column]
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

    def write_excel(self, df, file_path, type, target_folder):
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
        file_path = self.write_excel(df, file['upload'], type,folder)
        self.create_file_record(file_path,folder)
        self.insert_in_file_upload(file_path, file['name'], type, status)

    def load_source_df(self, file):
        if file['upload'].endswith('.xls') or file['upload'].endswith('.xlsx'):
            self.source_df = pd.read_excel(SITE_PATH + file['upload'], engine='openpyxl')
        elif file['upload'].endswith('.csv'):
            self.source_df = pd.read_csv(SITE_PATH + file['upload'])
        else:
            self.log_error(self.document_type, file['name'], 'The File should be XLSX or CSV')
            self.change_status('File upload', file['name'], 'Error')

    def get_columns_to_hash(self):
        return []

    def hashing_job(self):
        self.source_df['hash_column'] = ''
        columns_to_hash = self.get_columns_to_hash()
        for column in columns_to_hash:
            self.source_df['hash_column'] = self.source_df['hash_column'].astype(str) + self.source_df[column].astype(str)
        self.source_df['hash'] = self.source_df['hash_column'].apply(lambda x: hashlib.sha1(x.encode('utf-8')).hexdigest())

    def change_status(self, doctype, name, status):
        frappe.db.set_value(doctype,name,'status',status)

    def process(self):
        files = self.get_files_to_transform()
        if files == []:
            return None
        for file in files:
            self.change_status('File upload',file['name'],'In Process')
            self.load_source_df(file)
            if self.source_df.empty:
                self.log_error(self.document_type, file['name'], 'The File is Empty')
                self.change_status('File upload', file['name'], 'Error')
                continue

            if self.hashing == 1:
                self.hashing_job()
            self.load_target_df()
            if self.target_df.empty:
                self.new_records = self.source_df
                self.move_to_transform(file, self.new_records, 'Insert','Transform',False)

            else:
                merged_df = self.left_join(file)
                self.new_records = merged_df[merged_df['_merge'] == 'left_only']
                existing_df = merged_df[merged_df['_merge'] == 'both']
                self.modified_records, self.unmodified_records = self.split_modified_and_unmodified_records(
                    existing_df)
                self.move_to_transform(file, self.modified_records, 'Update','Transform',True)
                self.move_to_transform(file, self.unmodified_records, 'Skip','Bin',True, 'Skipped')
                self.move_to_transform(file, self.new_records, 'Insert','Transform',True)
            loader = Loader(self.document_type)
            loader.process()


            # Todo Call Loading process.


class BillTransformer(Transformer):
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


class ClaimbookTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Claim Book'
        self.document_type = 'ClaimBook'
        self.hashing = 1

    def get_columns_to_hash(self):
        return ['settled_amount','tds_amount']

    def load_target_df(self):
        query = f"""
                      SELECT 
                          name, hash
                      FROM 
                          `tab{self.document_type}`
                      """
        records = frappe.db.sql(query, as_list=True)
        self.target_df = pd.DataFrame(records,columns=['name','hash'])

    def get_join_columns(self):
        left_df_column = 'unique_id'
        right_df_column = 'name'
        return left_df_column, right_df_column

    def get_columns_to_prune(self):
        return ['name', '_merge','hash_x']

    def get_columns_to_check(self):
        return {'hash': 'hash_x'}
