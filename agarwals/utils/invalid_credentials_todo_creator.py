import frappe
from tfs.todo_creator import create_todo
from tfs.api_access import login, create_document,access_custom_api
from agarwals.utils.error_handler import log_error


class TPACredentialTODOCreator:

    def __init__(self):
        self.get_credential_data()

    def get_credential_data(self) -> None:
        """
            Usage : Retrieves credential data from the "Control Panel" document.
            Returns : None
        """
        control_panel = frappe.get_doc("Control Panel")
        if control_panel:
            self.user_id = control_panel.user_id
            self.password = control_panel.password
            self.url = control_panel.url
            self.allocated_user = control_panel.allocated_to
            self.is_api = int(control_panel.is_api)

    def login(self) -> object:
        """
            Usage :
                This method is used when to login on production environment.
            returns :
                Returns the Session (object)
        """
        login_status = login(username=self.user_id, password=self.password, url=self.url)
        if login_status:
            return login_status

    def get_invalid_credential_data(self) -> list | None:
        """
            Usage :
                Retrieves all invalid TPA login credentials with specific validations:
                Validation 1: The login credential has a status of 'Invalid'.
                Validation 2: If there is an associated ToDo entry with an 'Open' status, it is excluded to avoid duplication.
            Returns:
                list: A list of dictionaries containing invalid TPA login credentials.
                None : If no login credentials were found
        """
        condition = "tlc.status = 'Invalid' AND (td.status = 'Closed'OR td.status = 'Cancelled' OR td.status IS NULL) "
        invalid_credentials_query = f"""
                        SELECT tlc.* FROM `tabTPA Login Credentials` tlc
                        LEFT JOIN `tabToDo` td ON td.reference_name = tlc.name
                        WHERE {condition}
                        GROUP BY tlc.name ;
        """
        if self.is_api == 1:
            todo_data = access_custom_api(self.url,'get_todo_data')
            if todo_data:
                condition += f"AND tlc.name NOT IN {tuple(todo_data)}"
        invalid_credentials = frappe.db.sql(invalid_credentials_query, as_dict=True)
        return invalid_credentials if invalid_credentials else None
    def create_todo(self) -> None:
        """
        usage:
            Creates ToDo entries for invalid TPA login credentials.
        Raises:
            ValueError: If no invalid credential data is found.
        """

        invalid_credential_data = self.get_invalid_credential_data()
        if invalid_credential_data:
            for invalid_credential_doc in invalid_credential_data:
                try:
                    data = {
                        'date': frappe.utils.nowdate(),
                        'status': 'Open',
                        'priority': 'High',
                        'description': f"Invalid username or password :\nUser: {invalid_credential_doc.user_name}\nPassword: {invalid_credential_doc.password}\nTPA: {invalid_credential_doc.tpa}.",
                        "reference_type": 'TPA Login Credentials',
                        "reference_name": invalid_credential_doc.name,
                        "allocated_to": self.allocated_user
                    }
                    if self.is_api == 1:
                        create_document(session=self.login_session, url=self.url, content=data, doctype='ToDo')
                    else:
                        create_todo(data=data, commit=True)
                except Exception as e:
                    log_error(error=f"error occurs while creating todo for invalid logins {e}",
                              doc_name=invalid_credential_doc.name)
        else:
            raise ValueError("Invalid credential data not found")

    def process(self) -> None:
        """
        Usage:
            Processes the creation of ToDo entries for invalid TPA login credentials.
        Raises:
            Exception: Any exception raised during credential retrieval, login, or ToDo creation is caught and logged.
        """
        try:
            if self.is_api == 1:
                self.login_session = self.login()
                self.create_todo()
            else:
                self.create_todo()
        except Exception as e:
            log_error(error=e, doc_name="TPA Credential TODO Creator")

@frappe.whitelist()
def process_todo_creator():
    obj = TPACredentialTODOCreator()
    obj.process()
