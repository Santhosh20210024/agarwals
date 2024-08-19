import pandas as pd
import frappe
from agarwals.reconciliation.step.transform.transformer import StagingTransformer

FOLDER = "Home/DrAgarwals/"
IS_PRIVATE = 1
SITE_PATH = frappe.get_single('Control Panel').site_path


class AdviceTransformer(StagingTransformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Settlement Advice'
        self.document_type = 'Settlement Advice Staging'
        self.header = None
        self.clean_utr = 1
        self.utr_column_name = 'final_utr_number'
        self.rename_value = None
        self.list_of_char_to_replace = None

    def get_file_columns(self):
        return "upload,name,payer_type,is_mail"

    def clean_header(self, list_to_clean):
        cleaned_list = []
        for header in list_to_clean:
            for char_to_replace in self.list_of_char_to_replace:
                header = str(header).replace(char_to_replace, "").lower()
            cleaned_list.append(header)
        return cleaned_list

    def get_configuration(self):
        return frappe.get_single("Settlement Advice Configuration")

    def get_header_identification_keys(self, configuration):
        self.list_of_char_to_replace = eval(configuration.char_to_replace_in_header)
        header_identification_keys = eval(configuration.header_row_patterns)
        return self.clean_header(header_identification_keys)

    def get_source_column_dict(self, configuration):
        return eval(configuration.target_columns)

    def get_priority_list(self, value):
        if isinstance(value[0], list):
            return self.clean_header(value[0]), self.clean_header(value[1])
        else:
            return self.clean_header(value), []

    def find_header_key(self, list_of_values, identified_header_row, key):
        for columns in list_of_values:
            if columns in identified_header_row:
                self.rename_value[columns] = key
                return True
        return False

    def validate_header(self, header_row_index, source_column_list):
        self.source_df.columns = self.clean_header(self.source_df.loc[header_row_index].to_list())
        self.source_df = self.prune_columns(self.source_df)
        identified_header_row = self.clean_header(self.source_df.columns)
        identified_header_row.pop()
        self.rename_value = {}
        for key, value in source_column_list.items():
            p1_list, p2_list = self.get_priority_list(value)
            is_found = self.find_header_key(p1_list, identified_header_row, key)
            if not is_found and p2_list is not None:
                self.find_header_key(p2_list, identified_header_row, key)
        identified_header_row.append("index")
        return None, header_row_index, identified_header_row

    def verify_file(self, file, header_index):
        configured_customers = frappe.db.sql("""SELECT customer FROM `tabSA Configured Customers` WHERE parent = 'Settlement Advice Configuration' AND parentfield = 'tpa';""", as_list=True)
        if file["is_mail"] == 1 or [file["payer_type"]] in configured_customers:
            return True
        self.log_error(self.document_type, file['name'], f'No Configuration For the Payer: {file["payer_type"]}')
        self.update_status('File upload', file['name'], 'Error')
        return False

    def get_columns_to_prune(self):
        return ['name', '_merge', 'hash_x', 'hash_column']

    def get_column_name_to_convert_to_numeric(self):
        return ['claim_amount', 'settled_amount', 'tds_amount', 'disallowed_amount']

    def get_columns_to_fill_na_as_0(self):
        return ['claim_amount', 'settled_amount', 'tds_amount', 'disallowed_amount']

    def calculate_settled_amount(self, file, df):
        tpa_to_calculate_settled_amount = frappe.db.sql("""SELECT tpa FROM `tabSettled Amount Calculation Configuration` WHERE parent = 'Settlement Advice Configuration' AND parentfield = 'calculate_settled_amount';""", as_list=True)
        if [file["payer_type"]] not in tpa_to_calculate_settled_amount or 'linkedclaimnumber' in df.columns:
            return df
        has_tds_percentage = frappe.db.sql(f"""SELECT has_tds_percentage FROM `tabSettled Amount Calculation Configuration` WHERE parent = 'Settlement Advice Configuration' AND parentfield = 'calculate_settled_amount' AND tpa = '{file['payer_type']}';""", as_list=True)[0][0]

        def set_settled_amount(df):
            df['settled_amount'] = df['claim_amount'].astype(float) - df['tds_amount'].astype(float)
            return df

        def set_settled_amount_using_tds_percentage(df):
            df["tds_percentage"] = pd.to_numeric(df["tds_percentage"].fillna("0").astype(str).str.lstrip("0").str.strip().replace(
                        r"[\"\'?%,]", '', regex=True).replace("NOT AVAILABLE", "0").replace("", "0"), errors='coerce')
            df["calculated_tds"] = ((df["settled_amount"].astype(float) * df["tds_percentage"].astype(float))/100)
            if any(df["calculated_tds"].astype(float) == df["tds_amount"].astype(float)):
                df['claim_amount'] = df['settled_amount']
                df = set_settled_amount(df)
            return df.drop(columns = ["calculated_tds"])

        if has_tds_percentage == 0:
            df = set_settled_amount(df)
        else:
            df = set_settled_amount_using_tds_percentage(df)
        return df

    def clean_data(self, file, df):
        df = df.loc[:, ~df.columns.duplicated(keep='first')]
        df = self.convert_into_common_format(df, self.get_column_needed())
        df = self.fill_na_as_0(df)
        df = self.calculate_settled_amount(file, df)
        df["final_utr_number"] = df["utr_number"].fillna("0").astype(str).str.lstrip("0").str.strip().replace(
            r"[\"\'?]", '', regex=True).replace("NOT AVAILABLE", "0").replace("", "0")
        df["claim_id"] = df["claim_id"].fillna("0").astype(str).str.strip().replace(r"[\"\'?]", '', regex=True).replace(
            "", "0")
        df = self.format_date(df, eval(frappe.get_single('Bank Configuration').date_formats), 'paid_date')
        df = self.format_date(df, eval(frappe.get_single('Bank Configuration').date_formats), 'doa')
        df = self.format_date(df, eval(frappe.get_single('Bank Configuration').date_formats), 'dod')
        df = self.convert_into_common_format(df,self.get_column_needed())
        return df

    def get_columns_to_hash(self):
        return ["claim_id", "bill_number", "utr_number", "claim_status", "claim_amount", "disallowed_amount",
                "payers_remark", "settled_amount", "tds_amount"]

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
        left_df_column = "hash"
        right_df_column = "hash"
        return left_df_column, right_df_column

    def get_column_needed(self):
        return ["claim_id", "cl_number", "bill_number", "mrn", "utr_number", "final_utr_number", "claim_status", "paid_date", "insurance_company", "patient_name", "insurance_policy_number", "doa", "dod", "hospital_name", "bank_account_no", "bank_name", "bank_branch", "claim_amount", "settled_amount", "tds_amount", "disallowed_amount", "payers_remark", "hash", "file_upload", "transform", "index"]

    def extract(self, configuration, key, file):
        self.source_df.rename(columns=self.rename_value, inplace=True)
        if "claim_id" not in self.source_df.columns:
            self.log_error(self.document_type, file['name'], '"No Valid data header or file is empty')
            self.update_status('File upload', file['name'], 'Error')
            return False
        self.source_df = self.convert_into_common_format(self.source_df, self.get_column_needed())
        self.convert_column_to_numeric()
        self.source_df = self.clean_data(file, self.source_df)
        self.hashing_job()
        self.load_target_df()
        if self.target_df.empty:
            self.new_records = self.source_df
            self.move_to_transform(file, self.new_records, 'Insert', 'Transform', False)
            return True
        else:
            merged_df = self.left_join(file)
            if merged_df.empty:
                return False
            self.new_records = merged_df[merged_df['_merge'] == 'left_only']
            self.unmodified_records = merged_df[merged_df['_merge'] == 'both']
            self.move_to_transform(file, self.new_records, 'Insert', 'Transform', True)
            self.move_to_transform(file, self.unmodified_records, 'Skip', 'Bin', True, 'Skipped')
            return True
