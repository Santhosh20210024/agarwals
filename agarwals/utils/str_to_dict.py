import json

def cast_to_dic(variable_to_check):
    if type(variable_to_check) != str:
        return variable_to_check
    variable_to_check=json.loads(variable_to_check)
    return variable_to_check

        
