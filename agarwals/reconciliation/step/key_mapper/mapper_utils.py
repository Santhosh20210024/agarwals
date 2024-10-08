import frappe
import traceback
from agarwals.utils.error_handler import log_error
from tfs.orchestration import ChunkOrchestrator
from typing import Type, List, Dict, Any, Union


utr_key_query_mapper = {
                "Bank Transaction": """SELECT name, reference_number as key_id FROM `tabBank Transaction`
                                    WHERE reference_number != '0' AND reference_number IS NOT NULL 
                                    AND (custom_utr_key IS NULL or TRIM(custom_utr_key) = '') AND status != 'Cancelled'""",
                "ClaimBook": """SELECT name, utr_number as key_id FROM `tabClaimBook` 
                                WHERE utr_number != '0' AND utr_number IS NOT NULL AND TRIM(utr_number) != '' AND (utr_key IS NULL or TRIM(utr_key) = '')""",
                "Settlement Advice": """SELECT name, utr_number as key_id FROM `tabSettlement Advice` 
                                        WHERE utr_number != '0' AND utr_number IS NOT NULL AND TRIM(utr_number) != '' AND (utr_key IS NULL or TRIM(utr_key) = '')"""
               }

claim_key_query_mapper = {
                "Bill":"""SELECT name, 
                        claim_id AS claim_key_id, 
                        ma_claim_id AS ma_key_id 
                        FROM tabBill 
                        WHERE (claim_id IS NOT NULL AND TRIM(claim_id) != '0' 
                              AND TRIM(claim_id) != '' 
                              AND (claim_key IS NULL OR TRIM(claim_key) = ''))
                        OR (ma_claim_id IS NOT NULL 
                              AND TRIM(ma_claim_id) != '0' 
                              AND TRIM(ma_claim_id) != '' 
                              AND (ma_claim_key IS NULL OR TRIM(ma_claim_key) = ''))""",
                "ClaimBook":"""SELECT name, 
                            al_number AS al_key_id, 
                            cl_number AS cl_key_id 
                            FROM tabClaimBook 
                            WHERE (al_number IS NOT NULL 
                                  AND TRIM(al_number) != '0' 
                                  AND TRIM(al_number) != '' 
                                  AND (al_key IS NULL OR TRIM(al_key) = ''))
                            OR (cl_number IS NOT NULL 
                                AND TRIM(cl_number) != '0' 
                                AND TRIM(cl_number) != '' 
                                AND (cl_key IS NULL OR TRIM(cl_key) = ''))""",
                "Settlement Advice":"""SELECT name,
                                    claim_id as claim_key_id,
                                    cl_number as cl_key_id FROM `tabSettlement Advice` 
                                    WHERE (claim_id != '0' 
                                        AND TRIM(claim_id) != '' 
                                        AND claim_id IS NOT NULL 
                                        AND (claim_key is NULL or TRIM(claim_key) = '')) 
                                    OR ( cl_number != '0' 
                                        AND cl_number != ' ' 
                                        AND cl_number IS NOT NULL 
                                        AND (cl_key is NULL or cl_key = ''))"""
                }

def get_mapper_queries(type):
    if type == "UTRKey":
        return utr_key_query_mapper
    else:
        return claim_key_query_mapper

def process_records(mapper_class: Type, records: List[Dict[str, Any]]) -> str:
    """Process records using the specified mapper class."""
    return mapper_class(records).process()

@ChunkOrchestrator.update_chunk_status
def create_keys(
        mapper_class: Type[Union[
            "BillClaimKeyMapper",
            "ClaimBookClaimKeyMapper",
            "SettlementAdviceClaimKeyMapper",
            "BankTransactionUTRKeyMapper",
            "ClaimBookUTRKeyMapper",
            "SettlementAdviceUTRKeyMapper"
        ]],
        records: List[Dict[str, Any]]
    ) -> str:
        """Create keys using the given mapper class and records."""
        chunk_status = process_records(mapper_class, records)
        return chunk_status

@ChunkOrchestrator.update_chunk_status
def enqueue_record_processing(type: dict,
                              mappers: dict,
                              args: dict, 
                              job_name: str) -> str:
    chunk_status: str = "Processed"

    queries = get_mapper_queries(type)

    for record_type, query in queries.items():
        try:
            mapper_class = mappers[record_type]
            records = frappe.db.sql(query, as_dict=True)
            
            ChunkOrchestrator().process(
                create_keys,
                step_id=args["step_id"],
                is_enqueueable=True,
                chunk_size=args["chunk_size"],
                data_var_name="records",
                set_job_name=True,
                queue=args["queue"],
                is_async=True,
                timeout=18000,
                job_name=job_name,
                mapper_class=mapper_class,
                records=records
            )
        except Exception as e:
            log_error(f"Error While Enqueueing {record_type}: {str(e)}")
            chunk_status = "Error"

    return chunk_status