import frappe
from frappe.model.document import Document
from frappe.utils import today
from agarwals.utils import DatabaseUtils
from agarwals.utils.error_handler import log_error, CGException
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.reconciliation.step.transaction_creator import process_items
from tfs.orchestration import ChunkOrchestrator
from agarwals.reconciliation import (BANK_TRANSACTION_DOCTYPE,
                                     BANK_TRANSACTION_STAGING_DOCTYPE,
                                     BANK_UPDATE_DOCTYPE)
from agarwals.reconciliation.step.transaction_creator import BankStagingUtils

STATUS_PROCESSED = "Processed"
STATUS_SKIPPED = "Skipped"
STATUS_WARNING = "Warning"
STATUS_ERROR = "Error"

BANK_UPDATE_LOG = {
                    'U01': 'Success: Bank transaction processed successfully.',
                    'U02': 'Error: Transaction already reconciled.',
                    'U03': 'Warning: Reference number updated in Staging.',
                    'U04': 'Warning: Reference number updated in Transaction.',
                    'U05': 'Info: Payer name updated in both bank transaction staging and bank transaction.',
                    'U06': 'Info: Payer name updating while creation.',
                    'U07': 'Error: Processing error encountered.',
                    'U08': 'Error: Reference Number Not Found in Bank Transaction',
                    'U09': 'Info: Old bank transaction renamed',
                    'U10': 'Info: No changes found in bank transaction staging with this data',
                    'U11': 'Info: Internal ID Updated'
                  }

class BankUpdateException(CGException): 
    """Custom exception for handling bank transaction errors."""
    def __init__(self, method_name, error):
        super().__init__(method_name, str(error))

class BankUpdate(Document): 
    """Default Bank Update Document Class"""
    def autoname(self):
        if self.old_internal_id and self.staging_id is None:
            self.set_staging_id() # Only for internal id cases, don't give staging id in file.
        self.set_name()
        self.update_records()
    
    def set_staging_id(self):
        staging_ids = frappe.get_all(
            BANK_TRANSACTION_STAGING_DOCTYPE,
            filters={'internal_id': self.old_internal_id},
            pluck="name"
        )
        if len(staging_ids) > 1:
            frappe.throw('Several bank transaction staging documents have this Internal ID.')
        self.staging_id = staging_ids[0]
    
    def set_name(self):
        existing_adjustment_entries = frappe.get_all(
            BANK_UPDATE_DOCTYPE,
            filters={'staging_id': self.staging_id}
        )
        self.name = f"{self.staging_id}-{len(existing_adjustment_entries)}" if existing_adjustment_entries else self.staging_id

    def update_records(self):
        doc = frappe.get_doc('Bank Transaction Staging', self.staging_id)
        self.reference_number = doc.reference_number
        self.staging_status = doc.staging_status
        self.current_remark = doc.user_remark
        self.deposit = doc.deposit
        self.withdrawal = doc.withdrawal

class BankUpdateUtils: 
    @staticmethod
    def does_bank_transaction_exist(reference_number):
        """Check whether the bank transaction exists or not."""
        return BankStagingUtils().check_bt_exists(reference_number)
    
    @staticmethod
    def is_reconciled_transaction(item):
        return BankStagingUtils().is_bank_trasaction_payments_present(item['reference_number'])

class PayerUpdater:
    PAYER_UPDATE_QUERY_BANK_TRANSACTION_STAGING = """UPDATE `tabBank Transaction Staging` SET payer_name=%(party)s, payer_group=%(party_group)s"""
    PAYER_UPDATE_QUERY_BANK_TRANSACTION = """UPDATE `tabBank Transaction` SET custom_party_group=%(party_group)s, party=%(party)s"""

    def update_payer(self, item):
        """Execute payer update queries."""
        _values = {"party_group": item["party_group"], "party": item["party"]}
        frappe.db.sql(self.PAYER_UPDATE_QUERY_BANK_TRANSACTION_STAGING, values=_values)
        if not item["update_reference_number"] and BankUpdateUtils.does_bank_transaction_exist(item["reference_number"]):
            frappe.db.sql(self.PAYER_UPDATE_QUERY_BANK_TRANSACTION, values=_values)
            return BANK_UPDATE_LOG['U05']
        return BANK_UPDATE_LOG['U06']

class BankUpdateValidator:
    VALID_STAGING_STATUSES_INCLUSION = [STATUS_SKIPPED, STATUS_WARNING, STATUS_PROCESSED]
    VALID_STAGING_STATUSES_EXCLUSION = [STATUS_PROCESSED, STATUS_WARNING]
    
    def validate_item(self, item, is_inclusion=False):
        """Validates items based on inclusion or exclusion criteria."""
        if item['withdrawal']:
            return STATUS_ERROR, "Withdrawal transactions cannot be processed in the bank update."
        
        valid_statuses = self.VALID_STAGING_STATUSES_INCLUSION if is_inclusion else self.VALID_STAGING_STATUSES_EXCLUSION
        
        if item["staging_status"] not in valid_statuses:
            return STATUS_ERROR, "Invalid Bank Transaction Staging Status."
        
        if not is_inclusion and not BankUpdateUtils.does_bank_transaction_exist(item["reference_number"]):
            return STATUS_ERROR, "Bank Transaction Does Not Exist."
        
        return None, None

class BankUpdateProcessor(BankUpdateUtils):
    def __init__(self):
        self.validator = BankUpdateValidator()
        self.payer_updater = PayerUpdater()

    def get_update_list(self, _type):
        """Retrieves a list of bank updates based on the type."""
        return frappe.get_all(
            BANK_UPDATE_DOCTYPE,
            filters={"status": "Open", "operation_type": _type},
            fields=[
                "name","staging_id",
                "staging_status","withdrawal",
                "updated_internal_id","remark",
                "reference_number","update_reference_number",
                "current_remark","party","party_group",
            ],
        )

    def update_payer_info(self, item):
        """Updates payer information in the database."""
        staging_payer = frappe.db.get_value(
            BANK_TRANSACTION_STAGING_DOCTYPE, item["staging_id"], "payer_name"
        )
        if staging_payer != item["party"]:
           return self.payer_updater.update_payer(item)

    def mark_staging_retry(self, item):
        DatabaseUtils.update_doc(
            BANK_TRANSACTION_STAGING_DOCTYPE,
            item["staging_id"],
            update_reference_number=item["update_reference_number"],
            retry=1
        )

    def change_reference_number(self, item):
        """Manages reference number changes, including updating and clearing transactions."""
        if item['staging_status'] == STATUS_SKIPPED:
            self.mark_staging_retry(item)
            frappe.db.commit()
        elif (item['staging_status'] in [STATUS_PROCESSED, STATUS_WARNING] 
              and self.does_bank_transaction_exist(item["reference_number"])):
            self.mark_staging_retry(item)
            # DatabaseUtils.clear_doc(BANK_TRANSACTION_DOCTYPE, item["reference_number"])
            return BANK_UPDATE_LOG['U09']
        else:
            return BANK_UPDATE_LOG['U08']
    
    def process_inclusions(self, items):
        """Core methods for processing inclusions."""
        try:
            for item in items:
                bank_update_remark = []
                status, remark = self.validator.validate_item(item, is_inclusion=True)
                
                if status:
                    self.update_item_status(item["name"], status, remark)
                    continue

                self.handle_item_with_party(item, bank_update_remark) 
                self.handle_item_with_reference(item, bank_update_remark) 

                if(not BankUpdateUtils.does_bank_transaction_exist(item["reference_number"]) 
                   or BANK_UPDATE_LOG['U09'] in bank_update_remark):
                    self.process_new_item(item, bank_update_remark)
                else:
                    self.handle_existing_transaction(item, bank_update_remark)

                frappe.db.commit()
        except Exception as e:
            raise BankUpdateException("process_inclusions", e)

    def update_item_status(self, item_name, status, remark):
        """Update item status in the database."""
        DatabaseUtils.update_doc(
            BANK_UPDATE_DOCTYPE, 
            item_name, 
            status=status, 
            system_remark=remark
        )

    def handle_item_with_party(self, item, bank_update_remark):
        """Handle items that have a party."""
        if item["party"]:
            remark = self.update_payer_info(item)
            if remark:
                bank_update_remark.append(remark)
            frappe.db.commit()

    def handle_item_with_reference(self, item, bank_update_remark):
        """Handle items that have a reference number."""
        if item["update_reference_number"]:
            if BankUpdateUtils.is_reconciled_transaction(item):
                bank_update_remark.append(BANK_UPDATE_LOG['U02'])
                self.update_item_status(item["name"], STATUS_ERROR, "\n".join(bank_update_remark))
                return
            bank_update_remark.append(self.change_reference_number(item))

    def process_new_item(self, item, bank_update_remark):
        """Process a new bank transaction."""
        process_items({'name': item["staging_id"]})
        self.finalize_processing(item, bank_update_remark)

    def handle_existing_transaction(self, item, bank_update_remark):
        """Handle an existing bank transaction."""
        if not bank_update_remark:
            bank_update_remark.append(BANK_UPDATE_LOG['U10'])
            self.update_item_status(item["name"], STATUS_ERROR, "\n".join(bank_update_remark))
        elif(BANK_UPDATE_LOG['U02'] in bank_update_remark 
             or BANK_UPDATE_LOG['U07'] in bank_update_remark 
             or BANK_UPDATE_LOG['U08'] in bank_update_remark):
            self.update_item_status(item["name"], STATUS_ERROR, "\n".join(bank_update_remark))
        else:
            self.update_item_status(item["name"], STATUS_PROCESSED, "\n".join(bank_update_remark))

    def finalize_processing(self, item, bank_update_remark):
        """Update the corresponding status in bank transaction staging."""
        staging_item = frappe.get_doc('Bank Transaction Staging', item['staging_id'])
        status = self.determine_final_status(item, staging_item, bank_update_remark)
        self.update_item_status(item["name"], status, "\n".join([i for i in bank_update_remark if i != None]))
        frappe.db.commit()

    def determine_final_status(self, item, staging_item, bank_update_remark):
        """Determine the final status for the bank transaction."""
        if item['staging_status'] == STATUS_SKIPPED and staging_item.staging_status in [STATUS_PROCESSED, STATUS_WARNING]:
            bank_update_remark.append(BANK_UPDATE_LOG['U01'])     
            return STATUS_PROCESSED

        if item['staging_status'] == STATUS_WARNING and staging_item.staging_status == STATUS_PROCESSED:
            bank_update_remark.extend([
                BANK_UPDATE_LOG['U04'],
                BANK_UPDATE_LOG['U01']
            ])
            return STATUS_PROCESSED
        
        if (staging_item.staging_status in [STATUS_PROCESSED, STATUS_WARNING] 
            and BANK_UPDATE_LOG['U09'] in bank_update_remark):
            bank_update_remark.append(BANK_UPDATE_LOG['U01'])     
            return STATUS_PROCESSED

        if staging_item.staging_status == "Error":
            bank_update_remark.append(BANK_UPDATE_LOG['U07'])
            return STATUS_ERROR

        return STATUS_PROCESSED

    def get_remark(self, item):
        current_remark = item.get('current_remark') if item.get('current_remark', '') else ''
        if not item['remark']:
            item['remark'] = "Cancelled Manually"
        return f"{current_remark}\n{today()}: {item['remark']}\n"
    
    def process_exclusions(self, items):
        """Core methods for processing exclusions."""
        try:
            for item in items:
                status, remark = self.validator.validate_item(item)
                if status:
                    DatabaseUtils.update_doc(
                        BANK_UPDATE_DOCTYPE, 
                        item["name"],
                        status=status,
                        system_remark=remark
                    )
                else:
                    if self.is_reconciled_transaction(item):
                        DatabaseUtils.update_doc(
                            BANK_UPDATE_DOCTYPE,
                            item["name"],
                            status=STATUS_ERROR,
                            system_remark=BANK_UPDATE_LOG['U02']
                        )
                    else:
                        DatabaseUtils.clear_doc(BANK_TRANSACTION_DOCTYPE, item["reference_number"])
                        DatabaseUtils.update_doc(
                            BANK_TRANSACTION_STAGING_DOCTYPE,
                            item["staging_id"],
                            staging_status=STATUS_SKIPPED,
                            user_remark= self.get_remark(item)
                        )
                        DatabaseUtils.update_doc(
                            BANK_UPDATE_DOCTYPE,
                            item["name"],
                            status=STATUS_PROCESSED,
                            system_remark=None,
                        )

            frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            raise BankUpdateException("process_exclusions", e)
    
    def process_internal_id(self, items):
        for item in items:
            try:
                DatabaseUtils.update_doc(
                                BANK_TRANSACTION_STAGING_DOCTYPE,
                                item["staging_id"],
                                internal_id=item['updated_internal_id']
                            )
                
                if BankUpdateUtils.does_bank_transaction_exist(item['reference_number']):
                    DatabaseUtils.update_doc(
                                    BANK_TRANSACTION_DOCTYPE,
                                    item["reference_number"],
                                    is_submittable=True,
                                    custom_internal_id=item['updated_internal_id']
                                )
                    
                frappe.db.commit()
            except Exception as e:
                DatabaseUtils.update_doc(
                            BANK_UPDATE_DOCTYPE,
                            item["name"],
                            status=STATUS_ERROR,
                            system_remark=BANK_UPDATE_LOG["U07"] + str(e)
                        )
            DatabaseUtils.update_doc(
                    BANK_UPDATE_DOCTYPE,
                    item["name"],
                    status=STATUS_PROCESSED,
                    system_remark=BANK_UPDATE_LOG["U11"]
                )

    def start_inclusions(self):
        """Inclusion Starter"""
        update_inclusions_list = self.get_update_list("Inclusion")
        if update_inclusions_list:
            self.process_inclusions(update_inclusions_list)

    def start_exclusions(self):
        """Exclusion Starter"""
        update_exclusions_list = self.get_update_list("Exclusion")
        if update_exclusions_list:
            self.process_exclusions(update_exclusions_list)
    
    def update_internal_id(self):
        """Internal ID Updater"""
        update_internal_id_list = self.get_update_list("Internal ID")
        if update_internal_id_list:
            self.process_internal_id(update_internal_id_list)

    @ChunkOrchestrator.update_chunk_status
    def start_update(self):
        """Update Process"""
        status = STATUS_PROCESSED
        try:
            self.start_inclusions()
            self.start_exclusions()
            self.update_internal_id()
        except Exception as e:
            log_error(error=f"bank update(start_update):{e}", 
                      doc=BANK_UPDATE_DOCTYPE)
            status = STATUS_ERROR
        return status
    
@frappe.whitelist()
def process(args):
    """External API Access"""
    bank_update = BankUpdateProcessor()
    try:
        args = cast_to_dic(args)
        step_id = args["step_id"]
        ChunkOrchestrator().process(bank_update.start_update, step_id=step_id)
    except Exception as e:
        log_error(f"bank update(process):{e}", doc="Bank Update")
