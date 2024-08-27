from .direct_transformer import DirectTransformer
import frappe
import pandas as pd

class ClaimbookTransformer(DirectTransformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Claim Book'
        self.document_type = 'ClaimBook'
        self.hashing = 1
        self.clean_utr = 1
        self.utr_column_name = 'utr_number'
        self.is_truncate_excess_char = True

    def load_target_df(self):
        query = f"""
                      SELECT 
                          name, hash
                      FROM 
                          `tab{self.document_type}`
                      """
        records = frappe.db.sql(query, as_list=True)
        self.target_df = pd.DataFrame(records, columns=['name', 'hash'])