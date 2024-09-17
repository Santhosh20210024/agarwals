import frappe
from agarwals.utils.error_handler import log_error
from tfs.orchestration import ChunkOrchestrator
from typing import Type


@ChunkOrchestrator.update_chunk_status
def create_keys(mapper_class: Type[
    "BillClaimKeyMapper" or "ClaimBookClaimKeyMapper" or "SettlementAdviceClaimKeyMapper" or "BankTransactionUTRKeyMapper" or "ClaimBookUTRKeyMapper" or "SettlementAdviceUTRKeyMapper"],
                records: list) -> str:
    chunk_status = mapper_class(records).process()
    return chunk_status


@ChunkOrchestrator.update_chunk_status
def enqueue_record_processing(queries: dict,
                              mappers: dict,
                              args: dict, job_name: str) -> str:
    chunk_status: str = "Processed"
    for record_type, query in queries.items():
        try:
            mapper_class = mappers[record_type]
            records = frappe.db.sql(query, as_dict=True)
            ChunkOrchestrator().process(create_keys, step_id=args["step_id"], is_enqueueable=True,
                                        chunk_size=args["chunk_size"], data_var_name="records", set_job_name=True,
                                        queue=args["queue"], is_async=True, timeout=18000, job_name=job_name,
                                        mapper_class=mapper_class, records=records)
        except Exception as e:
            log_error("Error While Enqueueing: " + str(e), doc="Key Mapper")
            chunk_status = "Error"
    return chunk_status

