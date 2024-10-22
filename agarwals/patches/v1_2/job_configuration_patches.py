import frappe
from agarwals.utils.error_handler import log_error


class JobConfigurationPatch:
    def __init__(self):
        self.record_list = [
            {"name": "reconciliation_cron", "docstatus": 0, "idx": 0, "scheduler": "reconciliation_cron",
             "job_type": "Reconciliation", "config_name": "reconciliation_cron", "doctype": "Job Configuration",
             "step_config": [
                 {"name": "da1iqo2akv", "docstatus": 0, "idx": 1, "method": "agarwals.reconciliation.step.transform",
                  "priority": 1, "queue": "", "chunk_size": 0, "is_enabled": 1, "stop_if_error": 1,
                  "parameter": "{\n\"type\":\"debtors\",\n}",
                  "preview": "{\n \"type\": \"debtors\",\n \"step_id\": \"STP-......\"\n}", "number_of_workers": 0,
                  "parent": "reconciliation_cron", "parentfield": "step_config", "parenttype": "Job Configuration",
                  "doctype": "Step Configuration"},
                 {"name": "da1iju0nt1", "docstatus": 0, "idx": 2, "method": "agarwals.reconciliation.step.transform",
                  "priority": 1, "queue": "", "chunk_size": 0, "is_enabled": 1, "stop_if_error": 1,
                  "parameter": "{\n\"type\":\"claimbook\"\n}\n",
                  "preview": "{\n \"type\": \"claimbook\",\n \"step_id\": \"STP-......\"\n}", "number_of_workers": 0,
                  "parent": "reconciliation_cron", "parentfield": "step_config", "parenttype": "Job Configuration",
                  "doctype": "Step Configuration"}, {"name": "da1ie4mpvc", "docstatus": 0, "idx": 3,
                                                     "method": "agarwals.reconciliation.step.sales_invoice_creator",
                                                     "priority": 2, "queue": "long", "chunk_size": 100, "is_enabled": 1,
                                                     "stop_if_error": 1, "parameter": "",
                                                     "preview": "{\n \"step_id\": \"STP-......\",\n \"queue\": \"long\",\n \"chunk_size\": 100\n}",
                                                     "number_of_workers": 2, "parent": "reconciliation_cron",
                                                     "parentfield": "step_config", "parenttype": "Job Configuration",
                                                     "doctype": "Step Configuration"},
                 {"name": "da1idlp8ev", "docstatus": 0, "idx": 4, "method": "agarwals.reconciliation.step.transform",
                  "priority": 2, "queue": "", "chunk_size": 0, "is_enabled": 1, "stop_if_error": 1,
                  "parameter": "{\n\"type\":\"Settlement\"\n}\n",
                  "preview": "{\n \"type\": \"Settlement\",\n \"step_id\": \"STP-......\"\n}", "number_of_workers": 0,
                  "parent": "reconciliation_cron", "parentfield": "step_config", "parenttype": "Job Configuration",
                  "doctype": "Step Configuration"}, {"name": "da1i5a4pms", "docstatus": 0, "idx": 5,
                                                     "method": "agarwals.reconciliation.step.advice_creator",
                                                     "priority": 3, "queue": "long", "chunk_size": 100, "is_enabled": 1,
                                                     "stop_if_error": 1, "parameter": "",
                                                     "preview": "{\n \"step_id\": \"STP-......\",\n \"queue\": \"long\",\n \"chunk_size\": 100\n}",
                                                     "number_of_workers": 2, "parent": "reconciliation_cron",
                                                     "parentfield": "step_config", "parenttype": "Job Configuration",
                                                     "doctype": "Step Configuration"},
                 {"name": "da1i2ivlc7", "docstatus": 0, "idx": 6, "method": "agarwals.reconciliation.step.transform",
                  "priority": 3, "queue": "", "chunk_size": 0, "is_enabled": 1, "stop_if_error": 1,
                  "parameter": "{\n\"type\":\"transaction\"\n}\n",
                  "preview": "{\n \"type\": \"transaction\",\n \"step_id\": \"STP-......\"\n}", "number_of_workers": 0,
                  "parent": "reconciliation_cron", "parentfield": "step_config", "parenttype": "Job Configuration",
                  "doctype": "Step Configuration"}, {"name": "da1i8gva60", "docstatus": 0, "idx": 7,
                                                     "method": "agarwals.reconciliation.step.bank_transaction_processes.insurance_tagger",
                                                     "priority": 4, "queue": "long", "chunk_size": 100, "is_enabled": 1,
                                                     "stop_if_error": 1,
                                                     "parameter": "{\n\"doctype\":\"Bank Transaction Staging\"\n}",
                                                     "preview": "{\n \"doctype\": \"Bank Transaction Staging\",\n \"step_id\": \"STP-......\",\n \"queue\": \"long\",\n \"chunk_size\": 100\n}",
                                                     "number_of_workers": 2, "parent": "reconciliation_cron",
                                                     "parentfield": "step_config", "parenttype": "Job Configuration",
                                                     "doctype": "Step Configuration"},
                 {"name": "da1i2nkih7", "docstatus": 0, "idx": 8, "method": "agarwals.reconciliation.step.bank_transaction_processes.payer_match",
                  "priority": 5, "queue": "", "chunk_size": 0, "is_enabled": 1, "stop_if_error": 1, "parameter": "",
                  "preview": "{\n \"step_id\": \"STP-......\"\n}", "number_of_workers": 0,
                  "parent": "reconciliation_cron", "parentfield": "step_config", "parenttype": "Job Configuration",
                  "doctype": "Step Configuration"}, {"name": "da1i8o2jah", "docstatus": 0, "idx": 9,
                                                     "method": "agarwals.reconciliation.step.transaction_creator",
                                                     "priority": 6, "queue": "long", "chunk_size": 100, "is_enabled": 1,
                                                     "stop_if_error": 1,
                                                     "parameter": "{\n\"type\":\"transaction\"\n}\n",
                                                     "preview": "{\n \"type\": \"transaction\",\n \"step_id\": \"STP-......\",\n \"queue\": \"long\",\n \"chunk_size\": 100\n}",
                                                     "number_of_workers": 2, "parent": "reconciliation_cron",
                                                     "parentfield": "step_config", "parenttype": "Job Configuration",
                                                     "doctype": "Step Configuration"},
                 {"name": "da1iolmia0", "docstatus": 0, "idx": 10,
                  "method": "agarwals.reconciliation.step.key_mapper.claim_key_mapper", "priority": 7, "queue": "long",
                  "chunk_size": 100, "is_enabled": 1, "stop_if_error": 1, "parameter": "",
                  "preview": "{\n \"step_id\": \"STP-......\",\n \"queue\": \"long\",\n \"chunk_size\": 100\n}",
                  "number_of_workers": 2, "parent": "reconciliation_cron", "parentfield": "step_config",
                  "parenttype": "Job Configuration", "doctype": "Step Configuration"},
                 {"name": "da1it3at1j", "docstatus": 0, "idx": 11,
                  "method": "agarwals.reconciliation.step.key_mapper.utr_key_mapper", "priority": 7, "queue": "long",
                  "chunk_size": 100, "is_enabled": 1, "stop_if_error": 1, "parameter": "",
                  "preview": "{\n \"step_id\": \"STP-......\",\n \"queue\": \"long\",\n \"chunk_size\": 100\n}",
                  "number_of_workers": 2, "parent": "reconciliation_cron", "parentfield": "step_config",
                  "parenttype": "Job Configuration", "doctype": "Step Configuration"},
                 {"name": "da1i0av4pt", "docstatus": 0, "idx": 12, "method": "agarwals.reconciliation.step.matcher",
                  "priority": 8, "queue": "", "chunk_size": 0, "is_enabled": 1, "stop_if_error": 1, "parameter": "",
                  "preview": "{\n \"step_id\": \"STP-......\"\n}", "number_of_workers": 0,
                  "parent": "reconciliation_cron", "parentfield": "step_config", "parenttype": "Job Configuration",
                  "doctype": "Step Configuration"}, {"name": "da1ie6s0t2", "docstatus": 0, "idx": 13,
                                                     "method": "agarwals.reconciliation.step.payment_entry_creator",
                                                     "priority": 9, "queue": "long", "chunk_size": 100, "is_enabled": 1,
                                                     "stop_if_error": 1, "parameter": "",
                                                     "preview": "{\n \"step_id\": \"STP-......\",\n \"queue\": \"long\",\n \"chunk_size\": 100\n}",
                                                     "number_of_workers": 2, "parent": "reconciliation_cron",
                                                     "parentfield": "step_config", "parenttype": "Job Configuration",
                                                     "doctype": "Step Configuration"}],
             "__last_sync_on": "2024-09-13T14:02:32.597Z"}]

    def create_records(self):
        for record in self.record_list:
            try:
                doc = frappe.get_doc(record)
                doc.insert(ignore_permissions=True)
                frappe.db.commit()
            except Exception as e:
                log_error(e, "Job Configuration")

def execute():
    job_configuration_instance = JobConfigurationPatch()
    job_configuration_instance.create_records()