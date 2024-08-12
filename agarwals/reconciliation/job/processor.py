import frappe
from agarwals.reconciliation import worker


class Processor:
    def __init__(self):
        self.doc_name = ""
        self.parent_field_name = ""
        self.parent_doc_name = ""

    def create_doc(self, dict_value):
        try:
            doc = frappe.get_doc(dict_value).insert(ignore_permissions=True)
            frappe.db.commit()
            return doc
        except Exception as e:
            doc = dict_value["doctype"]
            self.raise_exception({"message": f"Doctype creation failed for {doc} with error {e}"})

    def get_step_list(self, job_config):
        if not job_config:
            self.raise_exception({"message": f"No Job Config to get step list"})
        try:
            step_list = frappe.db.get_all("Step Configuration", filters={"parent": job_config}, fields="*",order_by="priority")
            return step_list
        except Exception as e:
            self.raise_exception({"message": f"Error in Getting Step List for {job_config} and the error is {e}"})

    def raise_exception(self, exception):
        raise Exception(exception)

    def log_error(self, doctype_name, reference_name, error_message):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', doctype_name)
        error_log.set('reference_name', reference_name)
        error_log.set('error_message', error_message)
        error_log.save()

    def exit(self, e=None):
        if not e:
            return None
        if type(e.args) == tuple:
            if e.args[0] != None:
                (val,) = e.args
                if type(val) == dict:
                    if "doctype" in val and "message" in val:
                        self.log_error(val["doctype"], None, val["message"])
                    elif "message" in val:
                        self.log_error("Job", None, val["message"])
                else:
                    self.log_error("Job", None, e)
        else:
            (val,) = e.args
            if "doctype" in val and "message" in val:
                self.log_error(val["doctype"], None, val["message"])
            elif "message" in val:
                self.log_error("Job", None, val["message"])

    def get_data(self, filter_value):
        frappe.db.commit()
        data = frappe.get_all(self.doc_name, filter_value)
        return data

    def update_end_status(self, parent_id):
        try:
            if self.get_data({self.parent_field_name: parent_id, 'status': "Open"}):
                return None
            steps_list = frappe.get_all(self.doc_name, {self.parent_field_name: parent_id})
            parent_doc = frappe.get_doc(self.parent_doc_name, parent_id)
            if not steps_list or not parent_doc:
                self.raise_exception({"message": f"Either there is no step list or no parent doc for the Parent Id {parent_id}"})
            if self.get_data({self.parent_field_name: parent_id, "status": "Error"}):
                parent_doc.status = 'Error'
            elif len(steps_list) == len(
                    self.get_data({self.parent_field_name: parent_id, "status": 'Processed'})):
                parent_doc.status = 'Processed'
            else:
                return None
            parent_doc.end_time = frappe.utils.now_datetime()
            parent_doc.save()
            frappe.db.commit()
        except Exception as e:
            self.raise_exception(
                {"doctype": self.doc_name, "message": f"Failed To Change the step status and end time of due to {e}"})

    def start(self, name):
        pass

    def validate_process(self, name, parent_id):
        if not self.doc_name or not self.parent_field_name or not self.parent_doc_name:
            self.raise_exception({"message" : "No self Variable in the class the class is not initiated by child"})
        if not name:
            self.raise_exception({"doctype": self.doc_name, "message": "No Doc name"})
        if not parent_id:
            self.raise_exception({"doctype": self.doc_name, "message": "No Parent Id"})
        if self.get_data({self.parent_field_name: parent_id, 'status': "InProgress"}):
            return self.raise_exception(None)

    def process(self, name, parent_id):
        try:
            self.validate_process(name, parent_id)
            self.start(name)
            self.update_end_status(parent_id)
        except Exception as e:
            self.exit(e)
