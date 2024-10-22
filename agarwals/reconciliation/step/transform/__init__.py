from agarwals.factory.transformer_factory import get_transformer
import frappe
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from tfs.orchestration import ChunkOrchestrator


@ChunkOrchestrator.update_chunk_status
def transform(transformer_type: str) -> str:
    """Get the transformer object and call the process
    :param transformer_type:(str) the type of the transformation that need to be processed"""
    try:
        transformer = get_transformer(transformer_type)
        status = transformer.process()
        return status
    except Exception as e:
        log_error(e, 'Step')
        return "Error"


@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    ChunkOrchestrator().process(transform, step_id=args["step_id"], transformer_type=args["type"])
    return "Success"
