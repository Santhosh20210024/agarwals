from .transformer import Transformer

class DirectTransformer(Transformer):
    def __init__(self):
        super().__init__()

    def transform(self, file):
        if self.hashing == 1:
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
            existing_df = merged_df[merged_df['_merge'] == 'both']
            self.modified_records, self.unmodified_records = self.split_modified_and_unmodified_records(
                existing_df)
            self.move_to_transform(file, self.new_records, 'Insert', 'Transform', True)
            self.move_to_transform(file, self.modified_records, 'Update', 'Transform', True)
            self.move_to_transform(file, self.unmodified_records, 'Skip', 'Bin', True, 'Skipped')
        return True