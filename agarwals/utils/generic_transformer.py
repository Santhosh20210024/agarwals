import pandas as pd
import os
import shutil
from agarwals.utils.path_data import SITE_PATH
import frappe
import openpyxl
from datetime import date

class Transformer():
    def __init__(self):
        self.file_type = ''
        self.document_type = ''
        self.source_df = pd.DataFrame()
        self.new_records = pd.DataFrame()
        self.updated_records = pd.DataFrame()
        self.skipped_records = pd.DataFrame()


    def get_files(self):
        file_query = f"""SELECT 
                            upload,name 
                        FROM 
                            `tabFile upload` 
                        WHERE 
                            status = 'Open' AND document_type = '{self.file_type}'"""
        files = frappe.db.sql(file_query,as_dict=True)
        return files

    def get_columns_to_be_queried(self):
        return []

    def get_database_df(self,columns_to_be_queried):
        return []

    def get_columns_to_be_joined(self):
        self.left_df_column = ''
        self.right_df_column = ''
        return self.left_df_column,self.right_df_column

    def join_df(self,left_df,right_df):
        left_on, right_on = self.get_columns_to_be_joined()
        merged_df = left_df.merge(right_df, left_on = left_on, right_on = right_on, how = 'left', indicator = True, suffixes=('','_x'))
        return merged_df

    def remove_columns(self,df,columns_to_be_removed):
        for column in columns_to_be_removed:
            df = df.loc[:df.columns != column]
        return df

    def get_columns_to_be_removed(self):
        return []

    def get_columns_to_be_checked(self):
        return {}

    def get_updated_records(self,df):
        columns_to_be_checked = self.get_columns_to_be_checked()
        un_matched_df = pd.DataFrame()
        for left_column,right_column in columns_to_be_checked.items():
            un_matched_df = pd.concat([un_matched_df,df[~(df[left_column] == df[right_column])]],axis=0)
            df = df[df[left_column] == df[right_column]]
        return un_matched_df, df

    def throw_error(self,doctype_name,reference_name,error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name',reference_name)
        error_log.set('error_message',error_message)
        error_log.save()

    def write_excel_in_backend(self,df,file_path,type):
        file_path = file_path.replace('extract','transform').replace('.csv','.xlsx').replace('.xlsx','_'+type+'.xlsx')
        file_path_to_write = SITE_PATH + file_path
        df.to_excel(file_path_to_write,index=False)
        return file_path

    def create_file_record(self,file_url):
        is_private = 1
        folder = "Home/DrAgarwals/Transform"
        file_name = file_url.split('/')[-1]
        file = frappe.new_doc('File')
        file.set('file_name',file_name)
        file.set('is_private',is_private)
        file.set('folder',folder)
        file.set('file_url',file_url)
        file.save(ignore_permissions=True)

    def insert_in_file_upload(self,file_url,file_upload_name,type):
        file_upload = frappe.get_doc('File upload', file_upload_name)
        file_upload.append('transform',
                           {
                               'date' : date.today(),
                               'document_type' : self.document_type,
                               'type' : type,
                               'file_url' : file_url,
                               'status' : 'Open'
                           })
        file_upload.save(ignore_permissions=True)


    def process(self):
        files = self.get_files()
        for file in files:
            if file['upload'].endswith('.xls') or file['upload'].endswith('.xlsx'):
                self.source_df = pd.read_excel(SITE_PATH + file['upload'],engine='openpyxl')
            elif file['upload'].endswith('.csv'):
                self.source_df = pd.read_csv(SITE_PATH + file['upload'])
            else:
                self.throw_error(self.document_type,file['name'],'The File should be XLSX or CSV')

            if not self.source_df.empty:
                columns_to_be_queried = self.get_columns_to_be_queried()
                database_df = self.get_database_df(columns_to_be_queried)
                merged_df = self.join_df(self.source_df,database_df)
                self.new_records = merged_df[merged_df['_merge'] == 'left_only']
                columns_to_be_removed = self.get_columns_to_be_removed()
                self.new_records = self.remove_columns(self.new_records,columns_to_be_removed)
                existing_df = merged_df[merged_df['_merge'] == 'both']
                self.updated_records, self.skipped_records = self.get_updated_records(existing_df)
            else:
                self.throw_error(self.document_type, file['name'], 'The File was Empty')

            if not self.new_records.empty:
                file_path_after_written_insert = self.write_excel_in_backend(self.new_records,file['upload'],'insert')
                self.create_file_record(file_path_after_written_insert)
                self.insert_in_file_upload(file_path_after_written_insert,file['name'],'new')
            if not self.updated_records.empty:
                file_path_after_written_update = self.write_excel_in_backend(self.updated_records,file['upload'],'update')
                self.create_file_record(file_path_after_written_insert)
                self.insert_in_file_upload(file_path_after_written_insert, file['name'], 'new')
            if not self.skipped_records.empty:
                file_path_after_written_skip = self.write_excel_in_backend(self.skipped_records,file['upload'],'skip')
                self.create_file_record(file_path_after_written_insert)
                self.insert_in_file_upload(file_path_after_written_insert, file['name'], 'new')

class BillTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Debtor Report'
        self.document_type = 'Bill'

    def get_columns_to_be_queried(self):
        return ['name','status']

    def get_database_df(self, columns_to_be_queried):
        query = f"""
                     SELECT 
                         name, status
                     FROM 
                         `tab{self.document_type}`
                     """
        records = frappe.db.sql(query, as_dict=True)
        return records

    def get_columns_to_be_joined(self):
        self.left_df_column = 'Bill No'
        self.right_df_column = 'name'
        return self.left_df_column,self.right_df_column

    def get_columns_to_be_removed(self):
        return ['name','_merge','status_x']

    def get_columns_to_be_checked(self):
        return {'status':'status_x'}



class ClaimbookTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Claim Book'
        self.document_type = 'ClaimBook'
