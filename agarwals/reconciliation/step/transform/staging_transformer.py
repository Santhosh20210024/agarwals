from .transformer import Transformer

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

    def extract(self,configuration,key,file):
        return

    def extract_transactions(self, column):
        if pd.isna(self.source_df.at[0, column]):
            if len(self.source_df) > 1:
                self.source_df = self.source_df.loc[1:]
            else:
                return False
        null_index = self.source_df.index[self.source_df[column].isnull()].min()
        self.source_df = self.source_df.loc[:null_index - 1]
        return True

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
        self.source_df.columns = self.clean_header(self.source_df.columns)
        self.source_df = self.prune_columns(self.source_df)
        self.source_df.columns = cleaned_header_row
        is_extracted = self.extract(configuration,key,file)
        if not is_extracted:
            return False
        return True