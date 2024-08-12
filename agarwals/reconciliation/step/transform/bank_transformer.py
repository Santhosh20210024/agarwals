from .staging_transformer import StagingTransformer
import frappe
import re
import json

class BankTransformer(StagingTransformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Bank Statement'
        self.document_type = 'Bank Transaction Staging'
        self.header = None

    def get_file_columns(self):
        return "upload,name,date,bank_account"

    def clean_header(self, list_to_clean):
        return [self.trim_and_lower(value) for value in list_to_clean]

    def validate_header(self, header_row_index, source_column_list):
        identified_header_row = [self.trim_and_lower(column) for column in
                                 self.source_df.loc[header_row_index].to_list() if
                                 'nan' not in str(column) and str(column) != '*' and str(column) != '.']
        identified_header_row.pop()
        for key, columns in source_column_list.items():
            columns = [self.trim_and_lower(column) for column in columns]
            if set(identified_header_row) == set(columns):
                identified_header_row.append("index")
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

    def get_configuration(self):
        return frappe.get_single('Bank Configuration')

    def add_search_column(self):
        self.source_df['search'] = self.source_df['narration'].str.replace(r'[\'"\s]', '', regex=True).str.lower()


    def utr_validation(self, pattern, token):
        return bool(re.match(pattern, token))

    def extract_utr_by_length(self,narration, length, delimiters, pattern):
        if len(narration) < length:
            return None

        for delimiter in delimiters:
            for token in map(str.strip, narration.split(delimiter)):
                if len(token) == length and len(token.strip()) == length:
                    if self.utr_validation(pattern, token):
                        if not token.startswith("CX"):
                            return token

        return None

    def extract_utr(self, narration, reference, bank_account, delimiters):
        numeric = '^[0-9]+$'
        alphanumeric_pattern = '^[a-zA-Z]*[0-9]+[a-zA-Z0-9]*$'
        if "IMPS" in narration:
            length = 12
            pattern = numeric
        elif "NEFT" in narration or narration.startswith('N/'):
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
        elif "INFT" in narration:
            length = 12
            pattern = numeric
        else:
            if bank_account == 'BELGAUM - 32628850028 - STATE BANK OF INDIA' :
                pattern = alphanumeric_pattern
                utr_20 = self.extract_utr_by_length(reference, 20, delimiters, pattern )
                return utr_20
            else:
                return reference

        return self.extract_utr_by_length(narration, length, delimiters, pattern) or reference

    def extract_utr_from_narration(self, configuration):
        self.source_df['reference_number'] = self.source_df.apply(lambda row: self.extract_utr(str(row['narration']), str(row['utr_number']),str(row['bank_account']),eval(configuration.delimiters)), axis = 1)

    def validate_reference(self,source_ref):
        source_ref['reference_number'] = source_ref.apply(lambda row: 0 if str(row['reference_number']).isalpha() else row['reference_number'], axis=1)
        return source_ref

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
        is_extracted = self.extract_transactions("narration")
        if not is_extracted:
            self.log_error(self.document_type, file['name'], 'Transaction is Empty')
            self.update_status('File upload', file['name'], 'Error')
            return False
        if key in eval(configuration.banks_having_crdr_column):
            self.source_df['credit'] = self.source_df['amount'].where(self.source_df['cr/dr'].str.lower().str.contains('cr'))
            self.source_df['debit'] = self.source_df['amount'].where(self.source_df['cr/dr'].str.lower().str.contains('dr'))
        columns_to_select = self.get_column_needed()
        self.source_df = self.convert_into_common_format(self.source_df,columns_to_select)
        self.add_search_column()
        self.convert_column_to_numeric()
        self.extract_utr_from_narration(configuration)
        self.add_source_and_bank_account_column(file['name'], file['bank_account'])
        self.source_df = self.format_date(self.source_df,eval(configuration.date_formats),'date')
        self.source_df = self.fill_na_as_0(self.source_df)
        self.source_df = self.validate_reference(self.source_df)
        self.new_records = self.source_df
        self.move_to_transform(file, self.new_records, 'Insert', 'Transform', True)
        return True


class BankBulkTransformer(BankTransformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Bank Statement Bulk'
        self.header = 0

    def find_and_rename_column(self, df, list_to_check):
        header = df.columns.values.tolist()
        rename_value = {}
        for head in header:
            replace_str = head.strip().lower().replace(" ", "_").replace("-", "").replace("\'", "").replace("\"", "")
            if replace_str in list_to_check:
                rename_value[head] = replace_str
            else:
                raise Exception(f"Header is invalid {head}")
        return df.rename(columns=rename_value)


    def transform(self, file):
        self.source_df["file_upload"] = file['name']
        self.source_df = self.find_and_rename_column(self.source_df, self.get_columm_needed())
        configuration = frappe.get_single('Bank Configuration')
        if "date" in self.source_df.columns.values:
            self.source_df = self.format_date(self.source_df, eval(configuration.date_formats), 'date')
        self.extract_utr_from_narration(configuration)
        self.source_df['credit'] = self.source_df['deposit']
        self.source_df['debit'] = self.source_df['withdrawal']
        self.add_search_column()
        self.move_to_transform(file, self.source_df, 'Insert', 'Transform', False)
        return True