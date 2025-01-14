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
        self.format_numeric = False

    def load_target_df(self):
        query = f"""
                     SELECT 
                         name,hash_for_insert,hash_for_update,user_name,password,executing_method
                     FROM 
                         `tab{self.document_type}`
                     """
        records = frappe.db.sql(query, as_list=True)
        self.target_df = pd.DataFrame(records, columns=['name','hash_for_insert','hash_for_update','user_name','password','executing_method'])

    def create_patterns(self,url: str|None) -> str:
        return create_pattern(url)

    def get_downloader_name(self,pattern:str) -> str:
        """
        Matches the provided portal pattern to a downloader name.
        Args:
            pattern (str): The portal pattern to match against the downloader patterns.
        Returns:
            str: The name of the matching downloader if found; otherwise, an empty string.
        """
        downloader_name = [downloader_pattern['name'] for downloader_pattern in self.downloader_patterns if downloader_pattern.get('portal_pattern') == pattern]
        if downloader_name:
            return downloader_name[0]
        else:
            return ''

    def check_pattern_exists(self):
        """
        Checks for the existence of downloader patterns .
        Raises:
            ValueError: If one or more downloader patterns have a None  pattern,
                        indicating that the patterns are incomplete or invalid.
        """
        none_patterns = [downloader_pattern.get('name') for downloader_pattern in self.downloader_patterns if downloader_pattern.get('portal_pattern') is None]
        if none_patterns:
            raise ValueError(f"Downloader Pattern Not Found for {''.join(none_patterns)}")

    def __clean_data(self, df: pd.DataFrame, null_check_columns: List[str]) -> pd.DataFrame :
        """
        Cleans the input DataFrame by removing rows with null or empty values
        Args:
            df (pd.DataFrame): The input DataFrame to clean.
            null_check_columns (List[str]): The list of column names to check for
                                             null or empty values.
        Returns:
            pd.DataFrame: A cleaned DataFrame with rows containing null or empty
                           values in the specified columns removed.
        """
        null_check_mask = df[null_check_columns].isnull().any(axis=1) | (df[null_check_columns] == '').any(axis=1)
        error_record = df[null_check_mask]
        if not error_record.empty:
            self.error_records = pd.concat([self.error_records, error_record], ignore_index=True)
        cleaned_data = df if null_check_mask.empty else df[~null_check_mask]
        return cleaned_data

    def __hashing_job(self) -> pd.DataFrame:
        columns_to_hash = self.get_columns_to_hash()
        columns_to_hash.append('Password')
        hash_for_insert = self.hashing_job(return_df=True,update_source_df=False)
        hash_for_update = self.hashing_job(update_source_df=False,return_df=True,df=hash_for_insert,columns_to_hash=columns_to_hash,concatenated_column_name='concatenated_for_update',hash_column_name='Hash For Update')
        return hash_for_update

    def __process_feature_extraction(self,cleaned_data: pd.DataFrame) -> pd.DataFrame:
        """"
         Extracts features from the cleaned DataFrame
        Args:
            cleaned_data (pd.DataFrame): The cleaned DataFrame with the necessary
                                          data for feature extraction.
        Returns:
            pd.DataFrame: The updated DataFrame with new columns for patterns
                           and executing classes.
        """
        cleaned_data['pattern'] = cleaned_data['Url'].apply(self.create_patterns)
        cleaned_data['Executing Class'] = cleaned_data['pattern'].apply(self.get_downloader_name)
        self.source_df = cleaned_data
        prepared_data = self.__hashing_job()
        return prepared_data

    def __split_modified_and_unmodified_records(self,df:pd.DataFrame):
        self.modified_records,self.unmodified_records = self.split_modified_and_unmodified_records(df)
        if not self.modified_records.empty:
            self.modified_records['Retry'] = 1

    def __split_data(self,df: pd.DataFrame,file) -> bool:
        """
        Splits the new records , unmodified_records and modified_records
        """
        self.source_df = df
        merged_df = self.left_join(file)
        if merged_df.empty:
            return False
        self.new_records = merged_df[merged_df['_merge'] == 'left_only']
        both_matched = merged_df[merged_df['_merge'] == 'both']
        if not both_matched.empty:
            self.__split_modified_and_unmodified_records(both_matched)
        return True

    def transform(self,file):
        """
        Transforms the source DataFrame of the TPA Credentails and processes it for loading into a target system.
        Args:
            file: The file associated with the transformation process, which may be used for logging or storage.
        Returns:
            bool: True if the transformation process was successful; False otherwise.
        Raises:
            Exception: Raises an exception if an error occurs during the transformation process.
        """
        try:
            self.check_pattern_exists()
            cleaned_data = self.__clean_data(self.source_df,null_check_columns= self.get_columns_should_not_be_null())
            if not cleaned_data.empty:
                prepared_data = self.__process_feature_extraction(cleaned_data)
                refined_prepared_data = self.__clean_data(prepared_data,null_check_columns=['Executing Class'])
                if not refined_prepared_data.empty:
                    self.load_target_df()
                    if self.target_df.empty:
                        self.new_records = refined_prepared_data
                        self.move_to_transform(file, self.new_records, 'Insert', 'Transform', False)
                        return True
                    split_data = self.__split_data(refined_prepared_data,file)
                    if not split_data:
                        return False
                    self.move_to_transform(file, self.new_records, 'Insert', 'Transform', False)
                    self.move_to_transform(file, self.unmodified_records, 'Skip', 'Bin', False, 'Skipped')
                    self.move_to_transform(file, self.modified_records, 'Update', 'Bin', False)
                else:
                    return False

                return True
            else:
                return False
        except Exception as e:
            raise Exception(e)
        finally:
            self.move_to_transform(file, self.error_records, 'Skip', 'Transform/Error', False, 'Error')











