from .direct_transformer import DirectTransformer

class BillTransformer(DirectTransformer):
    def __init__(self):
        super().__init__()
        self.file_type = 'Debtors Report'
        self.document_type = 'Bill'
        self.hashing = 1

    def load_target_df(self):
        query = f"""
                     SELECT 
                         name, hash
                     FROM 
                         `tab{self.document_type}`
                     """
        records = frappe.db.sql(query, as_list=True)
        self.target_df = pd.DataFrame(records,columns = ['name','hash'])
