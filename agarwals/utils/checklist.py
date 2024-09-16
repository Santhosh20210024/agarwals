import frappe
from agarwals.utils.error_handler import log_error
from datetime import datetime, timedelta
import pandas as pd
from agarwals.reconciliation import chunk
import os
from agarwals.utils.str_to_dict import cast_to_dic
from typing import List


class Checker:
    def __init__(self):
        self.cases = {
            'C01': "Difference between Claim Amount and the total of Settled Amount, TDS Amount, and Disallowed Amount must be less than 9 in the current year Sales Invoice Report.",
            'C02': "The difference between the Total TDS, Total Disallowance, and Total Settled amounts and the respective sums of TDS, Disallowance, and Settled amounts in the current Sales Invoice Report.",
            'C03': "Difference between Deposit Amount and the Sum of Total Allocated and Total Un-allocated must be less than 9 in the current year Bank Transaction Report",
            'C04': "The difference between the Total Allocated Amount  and the respective sums of Allocated Amount in the current year Bank Transaction Report."
        }
        self.reports = []

    def __load_configurations(self):
        control_panel: object = frappe.get_doc("Control Panel")
        self.site_path: str = control_panel.site_path or self.raise_exception("Site path Not Found")
        self.project_folder: str = control_panel.project_folder or self.raise_exception("Project Folder Name not Found")
        self.mail_group: str = control_panel.check_list_email_group or self.raise_exception("No mail group Found")

    def __update_log(self) -> None:
        """
        Update the logs of Checklist
        """
        doc: object = frappe.new_doc("Check List Log")
        doc.job = self.job_id
        doc.date = frappe.utils.now_datetime().date()
        if not self.reports:
            self.reports.append({'name':'The job does not contain sufficient data to evaluate the conditions.','status':'Success'})
        for report in self.reports:
            doc.append('check_list_reference', {
                "name1": report.get('name'),
                "status": report.get('status'),
                "remarks": report.get('remarks')
            })
        doc.save()
        frappe.db.commit()


    def update_report(self, case_id: str, status: str, remarks: str | None = None) -> None:
        self.reports.append({"name": self.cases.get(case_id), "status": status, "remarks": remarks})

    def raise_exception(self, msg: str) -> None:
        raise Exception(msg)

    def is_exists(self, doctype: str) -> bool:
        count = len(frappe.get_list("File Records", {"reference_doc": doctype, "job": self.job_id}))
        if count <= 0:
            log_error(error=f"{doctype} not found for the job {self.job_id} - Checklist", status="INFO")
            return False
        return True


    def claim_amount_evaluation(self) -> None:
        """
            Evaluates the claim amount in the current Sales Invoice Report by summing the Settled Amount, TDS Amount,
            and Disallowed Amount. The total should be less than 9 to meet the specified condition.
        """
        claim_amount_evaluation_query = f"""
                                        SELECT * FROM `viewcurrent_year_si_checklist` 
                                        WHERE diff > 9 AND job = '{self.job_id}'
                                    """
        bill_number_list: List = frappe.db.sql(claim_amount_evaluation_query, pluck='bill_number')
        if len(bill_number_list) == 0:
            self.update_report('C01', 'Success')
        else:
            self.update_report('C01','Error',remarks=f"The listed bill numbers do not satisfy the condition: {', '.join(bill_number_list)}")


    def evaluate_total_vs_summed_amounts(self) -> None:
        """
        Evaluates the consistency between total amounts and their respective summed values.
        """
        query:List[dict] | None = frappe.db.sql(
            f""" SELECT * FROM `viewcumulative_current_year_sales_invoice` WHERE job = '{self.job_id}'""",
            as_dict=True)
        if query:
            cumulative_values:dict = query[0]
            remarks:str = f"""Settled Amount = f{cumulative_values.get('Total Settled Amount')}, Sum of Settled Amount = f{cumulative_values.get('Sum Settled Amount')} \n 
            TDS Amount = {cumulative_values.get('Total TDS Amount')} , Sum of TDS Amount = {cumulative_values.get('Sum TDS Amount')} \n
            Disallowance Amount = {cumulative_values.get('Total Disallowance Amount')} , Sum of Disallowance = { cumulative_values.get('Sum DIS')}
            """
            if (cumulative_values.get('Total Settled Amount') == cumulative_values.get('Sum Settled Amount')
                and cumulative_values.get('Total TDS Amount') == cumulative_values.get('Sum TDS Amount')
                and cumulative_values.get('Total Disallowance Amount') == cumulative_values.get('Sum DIS')):
                self.update_report(case_id='C02', status='Success', remarks=remarks)
            else:
                self.update_report(case_id='C02',status='Error',remarks=remarks)


    def deposit_amount_evaluation(self):
        """
            Evaluates Deposit amount in  current year Bank Transaction Report
            Total Deposit - (Total Allocated + Total Un-allocated) < 9
        """
        query:List = frappe.db.sql(f"""SELECT * FROM `viewcurrent_bank_report_checklist` WHERE job = '{self.job_id}' AND diff >= 9 """,pluck="UTR")
        if query:
            self.update_report(case_id="C03",status="Error",remarks=f"The listed UTR numbers do not satisfy the condition: {', '.join(query)}")
        else:
            self.update_report(case_id="C03",status="Success")

    def cumulative_alloacted_amount(self) -> None:
        """
        Evaluates the cumulative amount in the current year Bank Transaction Report
        Allocated Amount - Allocated Amount (Payment Entries) < 9
        """
        query:List[dict] = (frappe.db.sql
                (f"""
                   SELECT
                   vscbt.UTR_Number,
                   (vscbt.Total_Allocated) As Total_Allocated,
                   (vscbt.Current_Allocated_Amount) AS current_allocated,
                   (DIFF) AS Diff
                   FROM `tabFile Records` tfr JOIN `tabPayment Entry` tpe ON tpe.name = tfr.record
                   JOIN `viewcumulative_bank_report_checklist` vscbt ON vscbt.UTR_Number  = tpe.reference_no
                   WHERE job = '{self.job_id}'
                    ;
                """,as_dict=True))

        sum_current_allocated_amount:float = sum([amount.current_allocated for amount in query])
        sum_total_allocated_amount:float = sum([amount.Total_Allocated for amount in query])
        diff:float = sum([amount.Diff for amount in query if amount.Diff >= 9])
        if diff > 0:
            utr_number_list: List = [invalid_utr.UTR_Number for invalid_utr in query if invalid_utr.Diff >= 9]
        if sum_current_allocated_amount == sum_total_allocated_amount or diff == 0:
            self.update_report(case_id="C04",status='Success',remarks=f"Total allocated amount = {sum_total_allocated_amount} , Sum of current allocated amount = {sum_current_allocated_amount}")
        else:
            self.update_report(case_id="C04",status='Error',remarks=f"Total allocated amount = {sum_total_allocated_amount} , Sum current allocated amount = {sum_current_allocated_amount} and the listed UTR numbers do not satisfy the condition: {', '.join(utr_number_list)}")

    def current_year_bank_transaction(self) -> None:
        """
            Evaluates current year Bank Transaction Report
        """
        if self.is_exists(doctype="Payment Entry"):
            self.deposit_amount_evaluation()
            self.cumulative_alloacted_amount()

    def current_year_sales_invoice(self) -> None:
        """
            Evaluates current year Sales Invoice Report
        """
        if self.is_exists(doctype="Payment Entry"):
            self.claim_amount_evaluation()
            self.evaluate_total_vs_summed_amounts()

    def check_reports(self) -> None:
        """
        Evaluates reports
        """
        self.current_year_sales_invoice()
        self.current_year_bank_transaction()

    def __process_check_lists(self) -> None:
        self.check_reports()

    def generate_table(self) -> str:
        html_table = """
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th {
                background-color: #f2f2f2;
                padding: 10px;
                font-weight: bold;
                font-size: 16px;
                text-align: left;
                border-bottom: 2px solid #ddd;
            }
            td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .success {
                color: green;
                font-weight: bold;
            }
            .failure {
                color: red;
                font-weight: bold;
            }
            .remark-icon {
                display: inline-block;
                margin-right: 5px;
            }
        </style>
        <table cellpadding="5" cellspacing="0" border="1">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Remark</th>
                </tr>
            </thead>
            <tbody>
        """

        for item in self.reports:
            status_class = "success" if item.get('status', '') == "Success" else "failure"
            icon = "&#x2714;" if item.get('status',
                                          '') == "Success" else "&#x26A0;"  # Checkmark for success, warning sign for failure

            html_table += f"""
                <tr>
                    <td>{item.get('name', '')}</td>
                    <td class="{status_class}"><span class="remark-icon">{icon}</span>{item.get('status', '')}</td>
                    <td>{item.get('remarks', '')}</td>
                </tr>
            """

        html_table += """
            </tbody>
        </table>
        """

        return html_table

    def __send_mail(self) -> None:
        table = self.generate_table()
        message = f"""
            Hi All,
            <br>
            Below is the checklist report for the Batch {self.job_id},
            <br>
            <br>
            {table}
            <br><br>
            Thanks and Regards,
            <br><br>
            Claim Genie
        """
        frappe.sendmail(message=message, subject="Checklist Report", recipients='kramalingam@techfinite.com')

    def process(self, chunk_doc=None) -> None:
        try:
            self.job_id = 'JB-24-09-16-0000008803'
            if self.job_id:
                self.__load_configurations()
                self.__process_check_lists()
                self.__update_log()
                self.__send_mail()
            else:
                self.raise_exception("No Job ID Found to create checkList")
            chunk.update_status(chunk_doc, "Processed")
        except Exception as e:
            log_error(error=e)
            chunk.update_status(chunk_doc, "Error")



@frappe.whitelist(allow_guest=True)
def demo_process():
    checklist_instance = Checker()
    checklist_instance.process()


@frappe.whitelist()
def process(args):
    args = cast_to_dic(args)
    chunk_doc = chunk.create_chunk(args["step_id"])
    try:
        checklist_instance = Checker()
        frappe.enqueue(checklist_instance.process, queue='long', job_name=f"checklist - {frappe.utils.now_datetime()}",
                       chunk=chunk_doc)
    except Exception as e:
        chunk.update_status(chunk_doc, "Error")
        log_error(f"error While Processing checklist - {e}")

# @frappe.whitelist()
# def delete_checklist():
#     try:
#         path = frappe.get_single("Control Panel").site_path + f"/private/files/{PROJECT_FOLDER}/CheckList/"
#         if os.path.exists(path):
#             for file in os.listdir(path):
#                 file_path = os.path.join(path, file)
#                 if os.path.isfile(file_path):
#                     try:
#                         os.remove(file_path)
#                     except Exception as e:
#                         log_error(f"Error deleting file {file_path}: {e}")
#         else:
#             log_error("Path Not exits")
#     except Exception as e:
#         log_error(f"Error deleting checklist - {e}")
