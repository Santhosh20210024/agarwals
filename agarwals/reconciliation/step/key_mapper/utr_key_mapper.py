import frappe
from agarwals.reconciliation.step.key_mapper.key_mapper import KeyMapper
from agarwals.reconciliation.step.key_creator.utr_key_creator import UTRKeyCreator
from agarwals.reconciliation.step.key_mapper.utils import enqueue_record_processing
from agarwals.utils.error_handler import log_error


class UTRKeyMapper(KeyMapper):
    """ 
    UTRKeyMapper is used as base class for various UTR related doctypes

    Methods:
        map_key : return None
    """

    def __init__(self, records, record_type, query):
        super().__init__(records, record_type, "UTR Key")
        self.query = query

    def map_key(self, record):
        """ 
        Map Key is used to create a new key or to check whether there is any existing key for that variants,
        and update the corresponding values in respective doctypes.
        """
        try:
            key_id = self.get_striped_key_id(self.get_value(record, "key_id", ''))
            if key_id:
                KeyCreator = self.get_keycreator_obj(
                    UTRKeyCreator, key_id, record["name"]
                )
                key_id_variants = KeyCreator.get_variants()
                key = self.is_key_exist(key_id_variants, "UTR Key")
                if len(key) > 1:
                    log_error(
                        f"Multiple keys found: {str(key)}", "UTR Key", "Key Mapping"
                    )
                    return
                if not key:
                    key = KeyCreator.process(key_id_variants)
                
                self.update(self.query, key[0], record["name"])
        except KeyError as e:
            log_error(
                f"KeyError in map_key: {str(e)}",
                "UTR Key",
                self.record_type,
            )
            frappe.throw(f"KeyError while processing UTR keys: {str(e)}")

        except frappe.DoesNotExistError as e:
            log_error(
                f"DoesNotExistError in map_key: {str(e)}",
                "UTR Key",
                self.record_type,
            )
            frappe.throw(f"DoesNotExistError while processing UTR keys: {str(e)}")

        except frappe.ValidationError as e:
            log_error(
                f"ValidationError in map_key: {str(e)}",
                "UTR Key",
                self.record_type,
            )
            frappe.throw(f"ValidationError while processing UTR keys: {str(e)}")

        except Exception as e:
            log_error(
                f"Unexpected error in map_key: {str(e)}",
                "UTR Key",
                self.record_type,
            )
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
def process(args=None):  # Not Closed # Need to change according to the chunk
    try:
        # args = cast_to_dic(args)
        # chunk_size = int(args.get("chunk_size", 100))

        queries = {
            "Bank Transaction": """SELECT name, reference_number as key_id FROM `tabBank Transaction`
                                   WHERE reference_number != '0' AND reference_number IS NOT NULL 
                                   AND (custom_utr_key IS NULL or custom_utr_key = '') AND status != 'Cancelled'""",
            "ClaimBook": """SELECT name, utr_number as key_id FROM `tabClaimBook` 
                             WHERE utr_number != '0' AND utr_number IS NOT NULL AND ( utr_key IS NULL or utr_key = '')""",
            "Settlement Advice": """SELECT name, utr_number as key_id FROM `tabSettlement Advice` 
                                    WHERE utr_number != '0' AND utr_number IS NOT NULL AND ( utr_key IS NULL or utr_key = '')""",
        }

        mappers = {
            "Bank Transaction": BankTransactionUTRKeyMapper,
            "ClaimBook": ClaimBookUTRKeyMapper,
            "Settlement Advice": SettlementAdviceUTRKeyMapper,
        }

        for record_type, query in queries.items():
            process_records(query, mappers[record_type], 1000, None)

    except Exception as e:
        log_error("Error While Processing: " + str(e), doc="UTR Key")


def process_records(query, mapper_class, chunk_size, args):  # not closed
    records = frappe.db.sql(query, as_dict=True)
    if records:
        for index in range(0, len(records), chunk_size):
            # chunk_doc = chunk.create_chunk(args.get("step_id"))
            records_chunk = records[index : index + chunk_size]
            enqueue_record_processing(mapper_class, records_chunk)
    else:
        # finalize_chunk_processing(args.get("step_id"))
        pass