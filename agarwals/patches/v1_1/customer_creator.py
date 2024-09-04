import frappe
from agarwals.utils.error_handler import log_error
import numpy as np
import pandas as pd

class CustomerCreator:
    def create_customer(self,site_path):
        try:
            df = pd.read_csv(site_path +"Customer.csv")
            df = df.replace({np.nan: None})
            data_dict = df.to_dict(orient='records')
            for row_data in data_dict:
                customer_id = row_data.get('Customer Name')
                if not customer_id:
                    continue  
                try:
                    if not frappe.db.exists('Customer', {'customer_name': customer_id}):
                        customer_name = customer_id.strip().capitalize()
                        payer_priority= " "
                        payer_match = " "
                        if row_data.get('Payer Match'):
                            payer_match= row_data.get('Payer Match') 
                        if row_data.get('Payer Priority'):
                            payer_priority = row_data.get('Payer Priority')

                        customer_doc = frappe.new_doc('Customer')
                        customer_doc.update({
                            'customer_name': customer_name,
                            'customer_group': row_data.get('Customer Group'),  
                            'territory': row_data.get('Territory'),
                            'custom_payer_match': payer_match,
                            'custom_payer_priority' : payer_priority
                            })

                        customer_doc.save()
                        frappe.db.commit() 

                except Exception as e:
                    print(e)
                    log_error(e, "Customer", customer_id)

        except Exception as e:
            log_error("Error occurred while reading the file:", e, "Customer")

def execute():
    control_panel = frappe.get_single("Control Panel")
    if control_panel.site_path is None:
        raise ValueError("Site Path Not Found in CustomerCreator")
    site_path = f"{control_panel.site_path}/../../apps/agarwals/agarwals/master/"
    customer_instance = CustomerCreator()
    customer_instance.create_customer(site_path)
