from agarwals.factory.transformer_factory import get_transformer
import frappe
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error

@frappe.whitelist()
def process(args):
    try:
        args=cast_to_dic(args)
        transformer = get_transformer(args["type"])
        transformer.process(args)
        return "Success"
    except Exception as e:
        log_error(e,'Step')