import json
import frappe
from typing import  Any
def cast_to_dic(variable_to_check:Any) -> dict|Any:
    """"
    Converts String to dict
    if the param not in [dict,string]:
        returns the same value without converting
    """
    return frappe.parse_json(variable_to_check)
        
