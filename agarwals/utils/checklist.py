import frappe
from agarwals.utils.error_handler import log_error
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from tfs.orchestration.job import latest_job_name
from tfs.orchestration import ChunkOrchestrator, chunk
from typing import List,Any


class Checker:
    def __init__(self):
        self.cases = {
            'C01': " <b>Current year Sales Invoice Report : Total Claim Amount - ( Total Settled + Total TDS + Total Disallowance ) < ₹9 </b>: \n <br> Difference between Claim Amount and the total of Settled Amount, TDS Amount, and Disallowed Amount must be less than ₹9  in the current year Sales Invoice Report. \n ",
            'C02': " <b>Current Sales Invoice Report : Total TDS/Total Disallowance/Total Settled = Total of TDS/Disallowance/Settled </b>: \n <br> The difference between the Total TDS, Total Disallowance, and Total Settled amounts and the respective sums of TDS, Disallowance, and Settled amounts in the current Sales Invoice Report.",
            'C03': " <b>Current year Bank Transaction Report : Total Deposit - (Total Allocated + Total Un-allocated) < ₹9 </b>:\n <br> Difference between Total Deposit and the Sum of Total Allocated and Total Un-allocated must be less than ₹9 in the current year Bank Transaction Report. ",
            'C04': " <b>Current year Bank Transaction Report : Allocated Amount - Allocated Amount (Payment Entries) < ₹9  </b>:\n <br> The difference between the Total Allocated Amount  and the respective sums of Allocated Amount in the current year Bank Transaction Report."
        }
        self.reports = []

    def __load_configurations(self):
        """
        Load required configurations from control panel
        """
        self.control_panel: object = frappe.get_doc("Control Panel")
        mail_group: str = self.control_panel.check_list_email_group or self.raise_exception("No mail group Found")
        self.recipients: List = frappe.get_list("Email Group Member",{"email_group":mail_group,"unsubscribed":0},"email",pluck = "email") or self.raise_exception("There is no members active in the mail group")

    def __get_job_name(self,args:dict):
        """
         Get the job name based on manual trigger or scheduler
        :param args: list of arguments(dict)
        """
        self.job_id:str = None
        if args.get('is_manual'):
            self.job_id = self.control_panel.job_name
            self.control_panel.job_name = ''
            self.control_panel.is_manual = 0
            self.control_panel.save()
        else:
            step_doc = frappe.get_doc('Step',args.get('step_id'))
            self.job_id = step_doc.job_id

        if not self.job_id:
            raise ValueError("Job Name not found")

    def generate_table(self) -> str:
        """
        Generate the table using the report data for checklist
        :retruns : Html table with data (str)
        """
        html_table = """
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th {
                background-color: #2490EF;
                padding: 10px;
                font-weight: bold;
                font-size: 16px;
                text-align: center;
                border-bottom: 2px solid #ddd;
            }
            td {
                padding: 10px;
                border-bottom: 2px solid #ddd;
                border: 2px solid #ddd
                text-align: justify;
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
                    <th>Check List</th>
                    <th>Result</th>
                    <th>Remark</th>
                </tr>
            </thead>
            <tbody>
        """
        for item in self.reports:
            status_class = "success" if item.get('status', '') == "Success" else "failure"
            icon = "&#x2714;" if item.get('status','') == "Success" else "&#10060;"
            html_table += f"""
                <tr>
                    <td>{item.get('name', '')}</td>
                    <td class="{status_class}"><span class="remark-icon">{icon}</span></td>
                    <td>{item.get('remarks', '')}</td>
                </tr>
            """
        html_table += """
            </tbody>
        </table>
        """
        return html_table

    def __send_mail(self) -> None:
        """
         Generate the mail template and send the mail
        """
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
            <br>
            Claim Genie
            <br>
        """
        frappe.sendmail(message=message, subject=f"TFS: Reconciliation Checklist - {frappe.utils.nowdate()}", recipients=self.recipients)

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
            name = report.get('name')
            status = report.get('status')
            remarks = report.get('remarks')
            error_records = report.get('error_records')
            doc.append('check_list_reference', {
                "name1": name.replace("<br>", ""),
                "status": status,
                "remarks": f"Remarks = {remarks.replace('<br>','') if remarks else remarks}, Error Records = {error_records}"
            })
        doc.save()
        frappe.db.commit()


    def update_report(self, case_id: str, status: str, remarks: str | None = None,error_records: Any = None) -> None:
        self.reports.append({"name": self.cases.get(case_id), "status": status, "remarks": remarks, "error_records": error_records})

    def raise_exception(self, msg: str) -> None:
        raise Exception(msg)

    def get_total(self,data:List[dict],field_name:str) -> float | int:
        total = sum([value.get(field_name) for value in data ])
        return total

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
                                        WHERE job = '{self.job_id}'
                                    """
        claim_amount_evaluation: List[dict] = frappe.db.sql(claim_amount_evaluation_query,as_dict = True)
        total_claim_amount: float = self.get_total(data=claim_amount_evaluation,field_name='claim_amount')
        total_outstanding: float =  self.get_total(data=claim_amount_evaluation,field_name='outstanding_amount')
        total_settled_amount: float = self.get_total(data=claim_amount_evaluation,field_name='settled_amount')
        total_tds_amount: float = self.get_total(data=claim_amount_evaluation,field_name='tds_amount')
        total_disallowed_amount: float = self.get_total(data=claim_amount_evaluation,field_name='disallowed_amount')
        total: float = total_outstanding + total_tds_amount + total_settled_amount + total_disallowed_amount
        remarks:str = f"""Total Claim Amount - ( Total Settled + Total TDS + Total Disallowance ):\n {total_claim_amount} - {total} = 
                    {total_claim_amount - total} """
        bill_number_list: float = [bill.bill_number for bill in claim_amount_evaluation if bill.diff >= 9]
        if len(bill_number_list) == 0:
            self.update_report(case_id='C01',status='Success',remarks=remarks)
        else:
            error_records:str = f"The listed bill numbers do not satisfy the condition: {', '.join(bill_number_list)}"
            self.update_report(case_id='C01',status='Error',remarks=remarks,error_records=error_records)

    def evaluate_total_vs_summed_amounts(self) -> None:
        """
        Evaluates the consistency between total amounts and their respective summed values.
        """
        query:List[dict] | None = frappe.db.sql(
            f""" SELECT * FROM viewcumulative_current_year_sales_invoice_with_job WHERE job = '{self.job_id}'""",
            as_dict=True)
        if query:
            cumulative_values:dict = query[0]
            remarks:str = f"""Settled Amount = {cumulative_values.get('Total Settled Amount')} \n <br> Sum of Settled Amount = {cumulative_values.get('Sum Settled Amount')} \n 
            <br> TDS Amount = {cumulative_values.get('Total TDS Amount')} \n <br> Sum of TDS Amount = {cumulative_values.get('Sum TDS Amount')} \n
            <br> Disallowance Amount = {cumulative_values.get('Total Disallowance Amount')} \n <br> Sum of Disallowance = { cumulative_values.get('Sum Disallowance Amount')}
            """
            if (cumulative_values.get('Total Settled Amount') == cumulative_values.get('Sum Settled Amount')
                and cumulative_values.get('Total TDS Amount') == cumulative_values.get('Sum TDS Amount')
                and cumulative_values.get('Total Disallowance Amount') == cumulative_values.get('Sum Disallowance Amount')):
                self.update_report(case_id='C02', status='Success', remarks=remarks)
            else:
                self.update_report(case_id='C02',status='Error',remarks=remarks)


    def deposit_amount_evaluation(self):
        """
            Evaluates Deposit amount in  current year Bank Transaction Report
            Total Deposit - (Total Allocated + Total Un-allocated) < 9
        """
        query:List[dict] = frappe.db.sql(f"""SELECT * FROM `viewcurrent_bank_report_checklist` WHERE job = '{self.job_id}' """,as_dict=True)
        deposit: float =  self.get_total(data=query,field_name='Deposit')
        allocated_amount: float = self.get_total(data=query,field_name='Allocated Amount')
        unallocated_amount: float = self.get_total(data=query,field_name='Un-Allocated Amount')
        utr_number_list: List = [invalid_utr.UTR for invalid_utr in query if invalid_utr.get('diff') >= 9]
        remarks:str = f"Total Deposit - (Total Allocated + Total Un-allocated): <br> {deposit} - {allocated_amount} + {unallocated_amount} = {deposit - (allocated_amount+unallocated_amount)}"
        if utr_number_list:
            self.update_report(case_id="C03",status="Error",remarks=remarks,error_records=f"The listed UTR numbers do not satisfy the condition: {', '.join(utr_number_list)}")
        else:
            self.update_report(case_id="C03",status="Success",remarks=remarks)

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
        remarks:str = f"Total allocated amount = {sum_total_allocated_amount} <br> Sum of current allocated amount = {sum_current_allocated_amount}"
        if diff > 0:
            utr_number_list: List = [invalid_utr.UTR_Number for invalid_utr in query if invalid_utr.Diff >= 9]
        if sum_current_allocated_amount == sum_total_allocated_amount or diff == 0:
            self.update_report(case_id="C04",status='Success',remarks=remarks)
        else:
            self.update_report(case_id="C04",status='Error',remarks=remarks,error_records=f"The listed UTR numbers do not satisfy the condition: {', '.join(utr_number_list)}")

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

    @ChunkOrchestrator.update_chunk_status
    def process(self, args) -> str:
        """
        Processes a job based Checklist
            This method performs the following steps:
            1. Creates a chunk document using the provided step ID.
            2. Loads necessary configurations.
            3. Retrieves the job name based on manual trigger or scheduler.
            4. Processes the checklists associated with the job.
            5. If reports are generated, sends an email with the reports.
        """
        try:
            self.__load_configurations()
            self.__get_job_name(args)
            self.__process_check_lists()
            if self.reports:
                self.__send_mail()
            self.__update_log()
            return 'Processed'
        except Exception as e:
            log_error(error=e,doc="Check List Log")
            return 'Error'

@frappe.whitelist()
def process(args:str):
    args = cast_to_dic(args)
    try:
        checklist_instance = Checker()
        ChunkOrchestrator().process(checklist_instance.process,step_id=args["step_id"], is_enqueueable=True, queue=args["queue"],
                                is_async=True, timeout=3600 , args=args)
    except Exception as e:
        log_error(f"error While Processing checklist - {e}",doc="Check List Log")
