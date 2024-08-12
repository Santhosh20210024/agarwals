from .transformer import Transformer

class AdjustmentTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Bill Adjustment'
        self.document_type = 'Bill Adjustment'

    def find_and_rename_column(self,df,list_to_check):
        header = df.columns.values.tolist()
        rename_value = {}
        for head in header:
            replace_str = head.strip().lower().replace(" ","_").replace("-","").replace("\'","").replace("\"","")
            if replace_str in list_to_check:
                rename_value[head] = replace_str
            else:
               raise Exception(f"Header is invalid {head}")
        return df.rename(columns=rename_value)

    def transform(self, file):
        self.source_df["file_upload"] = file['name']
        self.source_df = self.find_and_rename_column(self.source_df,self.get_column_needed())
        configuration = frappe.get_single('Bank Configuration')
        if "posting_date" in self.source_df.columns.values:
            self.source_df = self.format_date(self.source_df,eval(configuration.date_formats),'posting_date')
        self.move_to_transform(file, self.source_df, 'Insert', 'Transform', False)
        return True