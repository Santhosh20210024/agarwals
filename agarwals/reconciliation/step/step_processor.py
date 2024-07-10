from agarwals.reconciliation.job.processor import Processor
from frappe.utils.backups import backup
import frappe
from agarwals.reconciliation import worker

class StepProcessor(Processor):
    def __init__(self):
        super().__init__()
        self.doc_name = "Step"
        self.parent_field_name = "job_id"
        self.parent_doc_name = "Job"

    def update_start_status(self, name):
        try:
            step_doc = frappe.get_doc('Step',name)
            step_doc.status = 'InProgress'
            step_doc.start_time = frappe.utils.now_datetime()
            step_doc.save()
            frappe.db.commit()
        except Exception as e:
            self.raise_exception({"doctype":"Step","message":f"Failed To Change the step status and start time of {name} due to {e}"})

    def check_previous_status(self, job_id):
        prev_step = frappe.db.sql(
            f"SELECT * FROM `tabStep` WHERE job_id = '{job_id}' AND priority = (SELECT MAX(priority) FROM `tabStep` WHERE status != 'Open'  AND job_id = '{job_id}' ) ",
            as_dict = True)
        status = []
        for i in range(0,(len(prev_step))):
            if prev_step[i].status == 'Processed' or (prev_step[i].status == 'Error' and prev_step[i].stop_if_error == 0):
                status.append('Execute')
            else:
                if prev_step[i].status == 'Error' and prev_step[i].stop_if_error == 1:
                    self.raise_exception({"message":f"Job Had Stopped Due to Error in {prev_step[i].name}"})
                status.append('Error')
        return "Execute" if 'Error' not in status else 'Break'

    def replace_placeholders(self, doc):
        param = doc.parameter
        replace_value = eval(doc.replace_value)
        if not param:
            self.raise_exception("No Parameter")
        if not replace_value:
            return eval(param)
        for key, value in replace_value.items():
            param = param.replace(key, str(doc[value]))
        return eval(param)

    def execute_method(self, steps):
        for i in range(0, len(steps)):
            self.update_start_status(steps[i].name)
            param = self.replace_placeholders(steps[i])
            frappe.call(steps[i].method + ".process", args = param)
            if steps[i].number_of_workers != 0:
                worker.add(steps[i].number_of_workers, param["queue"])

    def start(self, name):
        step_doc = frappe.get_doc("Step", name)
        job_config = frappe.db.sql(f"""SELECT parent FROM `tabStep Configuration` WHERE method = '{step_doc.method}'""", as_dict=True)
        step_config_list = frappe.db.sql(f"""SELECT * FROM `tabStep Configuration` WHERE parent = '{job_config[0]["parent"]}'""", as_dict=True)
        step_list = frappe.db.sql(f"""SELECT * FROM `tabStep` WHERE job_id='{step_doc.job_id}'""", as_dict=True)
        if len(step_config_list) == len(step_list):
            steps = frappe.db.sql(
                f"SELECT * FROM `tabStep` WHERE job_id = '{step_doc.job_id}' AND priority = (SELECT MIN(priority) FROM `tabStep` WHERE status = 'Open'  AND job_id = '{step_doc.job_id}' ) ",
                as_dict=True)
            if steps:
                if steps[0].priority == 1 and steps[0].status == 'Open':
                    self.execute_method(steps=steps)
                elif steps[0].priority != 1:
                    status = self.check_previous_status(step_doc.job_id)
                    if status == 'Execute':
                        self.execute_method(steps=steps)