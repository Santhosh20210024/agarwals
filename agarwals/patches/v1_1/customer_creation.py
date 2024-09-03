import frappe
from agarwals.utils.error_handler import log_error
import pandas as pd

class CustomerCreation:
    def create_customer(self):
        df = pd.read_csv("/home/frappe/frappe-bench/apps/agarwals/agarwals/master/Customer.csv")
        data_dict = df.to_dict(orient='records')  

        try:
            for row_data in data_dict:
                customer_id = row_data.get('Customer Name')
                if not customer_id:
                    continue  
                try:
                    if not frappe.db.exists('Customer', {'customer_name': customer_id}):
                        customer_name = customer_id.strip().capitalize()
                        customer_doc = frappe.new_doc('Customer')
                        customer_doc.update({
                            'customer_name': customer_name,
                            'customer_group': row_data.get('Customer Group'),  
                            'territory': row_data.get('Territory'), 
                            'name': customer_name
                        })

                        customer_doc.save()
                        frappe.db.commit() 

                except Exception as e:
                    log_error(e, "Customer", customer_id)

        except Exception as e:
            log_error("Error occurred while reading the file:", e, "Customer")

def execute():
    customer_instance = CustomerCreation()
    customer_instance.create_customer()
