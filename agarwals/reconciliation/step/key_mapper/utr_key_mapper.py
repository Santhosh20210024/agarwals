import frappe
from step.key_mapper.key_mapper import KeyMapper
from agarwals.utils.error_handler import log_error
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic


class UTRKeyMapper(KeyMapper):
    def __init__(self, records, doctype, query):
        super().__init__(records, doctype)
        self.query = query

    def map_key(self, record):
        try:
            key_id = str(record.get("key_id", "")).strip()
            if key_id:
                key_id_variants = self.get_key_id_variants(
                    "UTRKeyCreator", self.get_striped_key_id(key_id), record["name"]
                )
                keys = self.fetch_keys(key_id_variants, "UTR Key")

                if len(keys) > 1:
                    log_error(
                        f"Multiple keys found: {str(keys)}", "UTR Key", "Key Mapping"
                    )
                    return

                if not keys:
                    keys = self.create_key(
                        "UTRKeyCreator",
                        self.get_striped_key_id(key_id),
                        record["name"],
                        key_id_variants,
                    )

                self.update(self.query, keys[0], record["name"])

        except (
            KeyError,
            frappe.DoesNotExistError,
            frappe.ValidationError,
            frappe.DatabaseError,
        ) as e:
            log_error(
                f"DoesNotExistError or ValidationError or DatabaseError in map_key: {str(e)}",
                "UTR Key",
                self.doctype,
            )
            frappe.throw(f"Error while processing UTR keys: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error in map_key: {str(e)}", "UTR Key", self.doctype)
            frappe.throw(f"Unexpected error while processing UTR keys: {str(e)}")


class SettlementAdviceUTRKeyMapper(UTRKeyMapper):
    def __init__(self, records):
        super().__init__(
            records,
            "Settlement Advice",
            """UPDATE `tabSettlement Advice` SET utr_key = %(key)s WHERE name = %(name)s""",
        )


class BankTransactionUTRKeyMapper(UTRKeyMapper):
    def __init__(self, records):
        super().__init__(
            records,
            "Bank Transaction",
            """UPDATE `tabBank Transaction` SET custom_utr_key = %(key)s WHERE name = %(name)s""",
        )


class ClaimBookUTRKeyMapper(UTRKeyMapper):
    def __init__(self, records):
        super().__init__(
            records,
            "ClaimBook",
            """UPDATE `tabClaimBook` SET utr_key = %(key)s WHERE name = %(name)s""",
        )


@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        chunk_size = int(args.get("chunk_size", 100))

        queries = {
            "Bank Transaction": """SELECT name, reference_number as key_id FROM `tabBank Transaction`
                                   WHERE reference_number != '0' AND reference_number IS NOT NULL 
                                   AND custom_utr_key IS NULL AND status != 'Cancelled'""",
            "Claim Book": """SELECT name, utr_number as key_id FROM `tabClaimBook` 
                             WHERE utr_number != '0' AND utr_number IS NOT NULL AND utr_key IS NULL""",
            "Settlement Advice": """SELECT name, utr_number as key_id FROM `tabSettlement Advice` 
                                    WHERE utr_number != '0' AND utr_number IS NOT NULL AND utr_key IS NULL""",
        }

        mappers = {
            "Bank Transaction": BankTransactionUTRKeyMapper,
            "Claim Book": ClaimBookUTRKeyMapper,
            "Settlement Advice": SettlementAdviceUTRKeyMapper,
        }

        for record_type, query in queries.items():
            process_records(query, mappers[record_type], chunk_size, args)

    except Exception as e:
        handle_exception(args.get("step_id"), e)


def process_records(query, mapper_class, chunk_size, args):
    records = frappe.db.sql(query, as_dict=True)
    if records:
        for index in range(0, len(records), chunk_size):
            chunk_doc = chunk.create_chunk(args.get("step_id"))
            records_chunk = records[index : index + chunk_size]
            enqueue_record_processing(mapper_class, records_chunk, chunk_doc, args)
    else:
        finalize_chunk_processing(args.get("step_id"))


def enqueue_record_processing(mapper_class, records_chunk, chunk_doc, args):
    frappe.enqueue(
        mapper_class(records_chunk).process,
        queue=args.get("queue"),
        is_async=True,
        timeout=50000,
        records=records_chunk,
        chunk_doc=chunk_doc,
    )


def finalize_chunk_processing(step_id):
    chunk_doc = chunk.create_chunk(step_id)
    chunk.update_status(chunk_doc, "Processed")


def handle_exception(step_id, exception):
    if step_id:
        chunk_doc = chunk.create_chunk(step_id)
        chunk.update_status(chunk_doc, "Error")
    log_error(str(exception), "Step")