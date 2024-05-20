from agarwals.reconciliation.job.processor import Processor
import frappe

class JobProcessor(Processor):
    def __init__(self):
        super().__init__()

    def create_steps_for_job(self, job_id, job_config):
            step_list=self.get_step_list(job_config)
            for step in step_list:
                try:
                    step_doc = self.create_doc({
                        "doctype": "Step",
                        "method": step.method,
                        "priority": step.priority,
                        "job_id": job_id,
                        "parameter": step.parameter,
                        "stop_if_error": step.stop_if_error,
                        "status": "Open",
                        "replace_value": step.replace_value,
                        "number_of_workers":step.number_of_workers,
                        "queue":step.queue
                    })
                except Exception as e:
                    if step.stop_if_error == 1:
                        self.raise_exception({"message":f"{e} and The Process Cannot Be Continued as the stop if error is checked"})
                    else:
                        self.log_error("Step",reference_name=None,error_message=e)
                        continue

    def start(self, job_config):
        try:
            job_config_list = frappe.db.get_all("Job Configuration", filters={"name": job_config})
            if not job_config_list:
                self.raise_exception({"message":"No Job Configuration"})
            job = self.create_doc({
                "doctype": "Job",
                "start_time": frappe.utils.now(),
                "status": "InProgress",
            })
            self.create_steps_for_job(job.name, job_config)
        except Exception as e:
            self.exit(e)
