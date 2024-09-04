import frappe 
from agarwals.utils.error_handler import log_error

class CustomerGroupCreator :
    def create_custom_group(self):
        group_list =[{'name': 'TPA/INSURANCE', 'parent_customer_group': 'All Customer Groups'}, {'name': 'INSURANCE', 'parent_customer_group': 'All Customer Groups'}, {'name': 'Corporate', 'parent_customer_group': 'All Customer Groups'}, {'name': 'Govt - Specific', 'parent_customer_group': 'All Customer Groups'}, {'name': 'Government', 'parent_customer_group': 'All Customer Groups'}]

        for group in group_list:
            try:
                customer_group_record = frappe.new_doc('Customer Group')
                customer_group_record.update({
                    'name':group['name'],
                    'customer_group_name' : group['name'],
                    'parent_customer_group':group['parent_customer_group']
                })
                customer_group_record.save()
            except Exception as e:
                log_error(e,"Customer Group", group['name'])
                
def execute():
    customer_group_instance = CustomerGroupCreator()
    customer_group_instance.create_custom_group()