import frappe
from agarwals.utils.error_handler import log_error
from agarwals.utils.str_to_dict import cast_to_dic
from tfs.orchestration import ChunkOrchestrator


class MailRecordCreator:
    records = []
    file_upload_records = []
    staging_records = []
    advice_records = []
    matcher_records = []
    payment_entry_records = []

    def get_records(self):
        try:
            self.records = frappe.db.sql(f"select vfum.file_upload_name from viewFile_Upload_Mail vfum")
            # If no records are found, log the error and show message
            if not self.records:
                log_error("No records found: The mail has been sent till inserted!","Mail log")
                frappe.msgprint("The mail has been sent till New Files!")
                return False  # Early return to stop further processing
        except Exception as e:
            log_error(e, "Error fetching records")
            return False  # Early return to stop further processing
        return True
        
    def get_fileupload_records(self, fu_name):
        self.file_upload_records.append(frappe.db.sql(f"SELECT * from viewfile_upload_records vur WHERE vur.fu_name = '{fu_name}'", as_dict=True))

    def get_staging_records(self, fu_name):
        self.staging_records.append(frappe.db.sql(f"SELECT * from viewstaging_records vr WHERE file_upload_name = '{fu_name}'", as_dict=True))

    def get_advice_records(self, fu_name):
        self.advice_records.append(frappe.db.sql(f"SELECT * FROM viewadvice_records vr2 WHERE file_upload_name = '{fu_name}' ", as_dict=True))

    def get_matcher_records(self, fu_name):
        self.matcher_records.append(frappe.db.sql(f"SELECT * FROM viewmatcher_records vr3 WHERE file_upload_name = '{fu_name}'", as_dict=True))

    def get_payment_entry_records(self, fu_name):
        self.payment_entry_records.append(frappe.db.sql(f"SELECT * FROM viewpayment_entry_records ver WHERE file_upload_name = '{fu_name}'", as_dict=True))

    def process(self):
        try:
            if not self.get_records():
                return 
            for fu_name in self.records:
                try:
                    self.get_fileupload_records(fu_name[0])
                    self.get_staging_records(fu_name[0])
                    self.get_advice_records(fu_name[0])
                    self.get_matcher_records(fu_name[0])
                    self.get_payment_entry_records(fu_name[0])
                except Exception as e:
                    log_error(e, "File upload", fu_name)

        except Exception as e:
            log_error(e, "Mail log")


class ReportGenerator(MailRecordCreator):
    report_content = []

    def generate_fu_report(self):
        fu_records_table_html = f"""
            <label style="font-weight: bold; margin-bottom: 10px;">File Upload Records</label>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #2490EF;">
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">File Upload ID</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">File Name</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Status</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Inserted Records</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Updated Records</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Skipped Records</th>
                            </tr>
                        </thead>
                        <tbody>
            """
        
        for records in self.file_upload_records:
            for fu_records in records:
                    fu_records_table_html += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">{fu_records.get('fu_name')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{fu_records.get('file_name')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{fu_records.get('fu_status')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{fu_records.get('fu_inserted_records')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{fu_records.get('fu_updated_records')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{fu_records.get('fu_skipped_records')}</td>
                        </tr>
                    """
        fu_records_table_html += "</tbody></table>"
        return fu_records_table_html

    def generate_staging_report(self):
        staging_records_table_html = f"""
            <label style="font-weight: bold; margin-bottom: 10px;">Settlement Advice Staging Records</label>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #2490EF;">
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">File Upload ID</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Status</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Error Code</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Count</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Settled Amount</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">TDS Amount</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Disallowance Amount</th>
                            </tr>
                        </thead>
                        <tbody>
            """
        for records in self.staging_records:
            for record in records:
                    staging_records_table_html += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('file_upload_name')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('staging_status')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('staging_error_code')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('staging_count')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('staging_settled')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('staging_tds')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('staging_disallowance')}</td>
                        </tr>
                    """
        staging_records_table_html += "</tbody></table>"
        return staging_records_table_html

    def generate_advice_report(self):
        advice_records_table_html = f"""
            <label style="font-weight: bold; margin-bottom: 10px;">Settlement Advice Records</label>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #2490EF;">
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">File Upload ID</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Status</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Count</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Settled Amount</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">TDS Amount</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Disallowance Amount</th>
                                
                            </tr>
                        </thead>
                        <tbody>
            """
        for records in self.advice_records:
            for record in records:
                    advice_records_table_html += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('file_upload_name')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('advice_status')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('advice_count')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('advice_settled')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('advice_tds')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('advice_disallowance')}</td>
                            
                        </tr>
                    """
        advice_records_table_html += "</tbody></table>"
        return advice_records_table_html

    def generate_matcher_report(self):
        matcher_records_table_html = f"""
            <label style="font-weight: bold; margin-bottom: 10px;">Matcher Records</label>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #2490EF;">
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">File Upload ID</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Status</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Count</th>
                                
                            </tr>
                        </thead>
                        <tbody>
            """
        for records in self.matcher_records:
            for record in records:
                    matcher_records_table_html += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('file_upload_name')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('matcher_status')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('matcher_count')}</td>
                            
                        </tr>
                    """
        matcher_records_table_html += "</tbody></table>"
        return matcher_records_table_html

    def generate_payment_entry_report(self):
        payment_entry_records_table_html = f"""
            <label style="font-weight: bold; margin-bottom: 10px;">Payment Entry Records</label>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #2490EF;">
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">File Upload ID</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Status</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Count</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Settled Amount</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">TDS</th>
                                <th style="border: 1px solid #fff; padding: 8px; color : #fff;">Disallowance</th>
                            </tr>
                        </thead>
                        <tbody>
            """
        for records in self.payment_entry_records:
            for record in records:
                    payment_entry_records_table_html += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('file_upload_name')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('pe_status')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('pe_count')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('pe_settled')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('pe_tds')}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{record.get('pe_disallowance')}</td>
                        </tr>
                    """
        payment_entry_records_table_html += "</tbody></table>"
        return payment_entry_records_table_html

    def generate_report(self):
        self.report_content = (
            f"{self.generate_fu_report()}\n\n"
            f"{self.generate_staging_report()}\n\n"
            f"{self.generate_advice_report()}\n\n"
            f"{self.generate_matcher_report()}\n\n"
            f"{self.generate_payment_entry_report()}"
        )

    def process(self):
        super().process()
        if self.records :
            self.generate_report()


class MailSender(ReportGenerator):

    def send_email(self, report_content , mail_group):
        try:
            subject = f"TFS ClaimGenie SA Records Report {frappe.utils.nowdate()}"
            message=f"""
                Hello all,<br>
            Below is the ClaimGenie SA Records Report. 
            <br><br>
            {report_content}
            <br>
            <div class = info >
            <h3 style= "margin :0"> Info - Staging error codes </h3>
            S100 : Settlement Advice Already Exist <br>
            S101 : UTR and claim Id is Mandatory <br>
            S102 : Settled amount is Mandatory <br>
            S103 : UTR must in Non-Exponential Formate <br>
            S104 : System Error <br>
            S105 : Amount Should Not Be Negative <br>
            S106 : Already Processed Cannot Be Updated <br>
            </div><br><br>
            Thanks and regards,
            <br>ClaimGenie 
            """

            if mail_group:
                recipients = frappe.get_list('Email Group Member', {'email_group': mail_group} , pluck='email')
                if recipients:
                    frappe.sendmail(
                        recipients = recipients,
                        subject = subject,
                        content = message,
                        delayed = False
                    )
            else:
                log_error('No Mail Group Configured for SA Report')

        except Exception as e:
            log_error(e, "Mail log")

    def process(self,mail_group):
        super().process()
        if self.records:   
            self.send_email(report_content=self.report_content, mail_group=mail_group)
    
class FileUploadUpdater(MailSender):

    def update_file_upload(self):
        file_records = self.records
        if file_records:
            for file_record in file_records :
                for record in file_record :
                    try :
                        fu_record = frappe.get_doc("File upload", record)
                        fu_record.update({
                            'sa_mail_sent' :1
                        })
                        fu_record.save()
                    except Exception as e:
                        log_error("Error Ocuured while Update :{e}","File upload",record)

    @ChunkOrchestrator.update_chunk_status
    def process(self, mail_group: str) -> str:
        super().process(mail_group)
        if self.records:
            self.update_file_upload()
        return "Processed"


@ChunkOrchestrator.update_chunk_status
def send_sa_mail(args: dict) -> str:
    try:
        controlpanel = frappe.get_single("Control Panel")
        if controlpanel.sa_report_email_group is None:
            raise ValueError("Email Group Not Found in SA Report")
        mail_sender = FileUploadUpdater()
        ChunkOrchestrator().process(mail_sender.process, step_id=args.get("step_id"), is_enqueueable=True,
                                    queue=args.get('queue', "long"),
                                    job_name=f"sa mail sender - {frappe.utils.now_datetime()}",
                                    mail_group=controlpanel.sa_report_email_group)
        return "Processed"
    except Exception as e:
        log_error(e, doc_name="Mail log")
        return "Error"


@frappe.whitelist()
def process(args: str | dict) -> None:
    args = cast_to_dic(args)
    ChunkOrchestrator().process(send_sa_mail, step_id=args.get("step_id"), args=args)
