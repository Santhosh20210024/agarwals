import frappe
import pandas as pd
from agarwals.reconciliation.doctype.sa_downloader_configuration import create_pattern
from agarwals.reconciliation.step.transform.transformer import Transformer
from typing import List
import hashlib
import re

class TpaCredentialsTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.file_type: str = 'TPA Credentials'
        self.document_type: str = 'TPA Login Credentials'
        self.downloader_patterns: List[dict] =  frappe.get_all(doctype="SA Downloader Configuration",filters = {},fields="name,portal_pattern")
        self.error_records = pd.DataFrame()

    def load_target_df(self):
        query = f"""
                     SELECT 
                         name, hash ,user_name,password,executing_method
                     FROM 
                         `tab{self.document_type}`
                     """
        records = frappe.db.sql(query, as_list=True)
        self.target_df = pd.DataFrame(records, columns=['name', 'hash','user_name','password','executing_method'])

    def create_patterns(self,url: str|None) -> str:
        return create_pattern(url) if url else 'Url not found'

    def match_downloader_patterns(self,pattern:str) -> str:
        downloader_name = [pattern['name'] for pattern in self.downloader_patterns if pattern['portal_pattern'] == pattern]
        return downloader_name[0] if downloader_name else 'Not Found'

    def check_pattern_exists(self):
        none_patterns = [downloader_pattern.get('name') for downloader_pattern in self.downloader_patterns if downloader_pattern.get('portal_pattern') is None]
        if none_patterns:
            raise ValueError(f"Downloader Pattern Not Found for {''.join(none_patterns)}")

    def get_null_ckeck_mask(self,df,null_check_columns:List[str]) -> pd.DataFrame:
        null_check_mask = df[null_check_columns].isnull().any(axis=1) | (df[null_check_columns] == '').any(axis=1)
        return null_check_mask


    def __clean_data(self, df: pd.DataFrame, null_check_columns: List[str]) -> pd.DataFrame :
        null_check_mask = self.get_null_ckeck_mask(df,null_check_columns)
        error_records = df[null_check_mask]
        if not error_records.empty:
            pd.concat([self.error_records, error_records], ignore_index=True)
        cleaned_data = df if null_check_mask.empty else df[[~null_check_mask]]
        return cleaned_data if not cleaned_data.empty() else False


    def __process_feature_extraction(self,cleaned_data: pd.DataFrame) -> pd.DataFrame:
        cleaned_data['pattern'] = cleaned_data['Url'].apply(self.create_patterns)
        cleaned_data['Executing Class'] = cleaned_data['pattern'].apply(self.match_executing_class)
        self.source_df = cleaned_data
        self.hashing_job()
        return cleaned_data


    def __create_hash(self,df: pd.DataFrame,columns_to_hash:List[str]) -> pd.DataFrame:
        for column in columns_to_hash:
            df['hash_column'] = df['hash_column'].astype(str) + df[column].astype(str)
        df['hash'] = df['hash_column'].apply(lambda x: hashlib.sha1(x.encode('utf-8')).hexdigest())
        return df


    def __split_update_and_unmodified_records(self,df:pd.DataFrame,file):
        self.source_df = self.__create_hash(df,['Password'].extend(self.get_columns_to_hash()))
        self.target_df = self.__create_hash(self.target_df,columns_to_hash=['user_name','password','executing_method'])
        merged_df = self.left_join(file)
        self.unmodified_records = merged_df[merged_df['_merge'] == 'both']
        self.modified_records = merged_df[merged_df['_merge'] == 'left_only']

    def __split_data(self,df: pd.DataFrame,file) -> bool:
        self.source_df = df
        merged_df = self.left_join(file)
        if merged_df.empty:
            return False
        self.new_records = merged_df[merged_df['_merge'] == 'left_only']
        both_matched = merged_df[merged_df['_merge'] == 'both']
        if both_matched:
            self.__split_update_and_unmodified_records(both_matched,file)
        return True

    def transform(self,file):
        self.check_pattern_exists()
        cleaned_data = self.__clean_data(self.source_df,null_check_columns= ['Password','User Name','Url'])
        if not cleaned_data.empty:
            prepared_data = self.__process_feature_extraction(cleaned_data)
            refined_prepared_data = self.__clean_data(prepared_data,null_check_columns=['Executing Class'])
            if not refined_prepared_data.empty:
                self.load_target_df()
                if self.target_df.empty:
                    self.new_records = refined_prepared_data
                    self.move_to_transform(file, self.new_records, 'Insert', 'Transform', False)
                    return True
                split_data = self.__split_data(refined_prepared_data, file)
                if not split_data:
                    self.move_to_transform(file, self.error_records, 'Skip', 'Error', 'Error')
                    return False
                self.move_to_transform(file, self.new_records, 'Insert', 'Transform', False)
                self.move_to_transform(file, self.unmodified_records, 'Skip', 'Bin', False, 'Skipped')
                self.move_to_transform(file, self.modified_records, 'Update', 'Bin', False)
            else:
                return False
            self.move_to_transform(file,self.error_records,'Skip','Error','Error')
            return True
        else:
            self.move_to_transform(file, self.error_records, 'Skip', 'Error', 'Error')
            return False









