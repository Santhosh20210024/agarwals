import frappe

class ViewCreator:
    def file_upload_mail_view(self):
        # Create or replace view 'viewFile_Upload_Mail_log'
        frappe.db.sql("""CREATE or REPLACE VIEW viewFile_Upload_Mail AS
            SELECT
                tfu.name AS file_upload_name,
                tfu.document_type AS file_type,
                tfu.total_records AS fil_total_records
            FROM
                `tabFile upload` tfu
            WHERE
                tfu.is_bot = 0
                AND tfu.document_type = 'Settlement Advice'
                AND tfu.sa_mail_sent = 0;
        """)

    def file_upload_view(self):
        # Create or replace view 'viewfile_upload_records'
        frappe.db.sql("""CREATE or REPLACE VIEW viewfile_upload_records AS
            SELECT
                tfu.name AS fu_name,
                tfu.file as file_name,
                tfu.status AS fu_status,
                tfu.insert_records AS fu_inserted_records,
                tfu.update_records AS fu_updated_records,
                tfu.skipped_records AS fu_skipped_records
            FROM
                `tabFile upload` tfu
            JOIN viewFile_Upload_Mail vfum ON tfu.name = vfum.file_upload_name;
        """)

    def staging_view(self):
        # Create or replace view 'viewstaging_records'
        frappe.db.sql("""CREATE or REPLACE VIEW viewstaging_records AS
            SELECT
                tsas.status AS staging_status,
                tsas.error_code AS staging_error_code,
                COUNT(tsas.name) AS staging_count,
                SUM(tsas.settled_amount) AS staging_settled,
                SUM(tsas.tds_amount) AS staging_tds,
                SUM(tsas.disallowed_amount) AS staging_disallowance,
                vfum.file_upload_name 
            FROM
                `tabSettlement Advice Staging` tsas
            JOIN viewFile_Upload_Mail vfum ON tsas.file_upload = vfum.file_upload_name
            GROUP BY
                vfumv.file_upload_name,
            tsas.error_code,
            tsas.status ;
            """)

    def advice_view(self):
        # Create or replace view 'viewadvice_records'
        frappe.db.sql("""CREATE or REPLACE VIEW viewadvice_records AS
            SELECT
                tsa.status AS advice_status,
                COUNT(tsa.name) AS advice_count,
                SUM(tsa.settled_amount) AS advice_settled,
                SUM(tsa.tds_amount) AS advice_tds,
                SUM(tsa.disallowed_amount) AS advice_disallowance,
                vfum.file_upload_name 
            FROM
                `tabSettlement Advice` tsa
            JOIN viewFile_Upload_Mail vfum ON tsa.file_upload = vfum.file_upload_name
            GROUP BY
                vfumv.file_upload_name ,
                tsa.status;
                """)

    def matcher_view(self):
        # Create or replace view 'viewmatcher_records'
        frappe.db.sql("""CREATE or REPLACE VIEW viewmatcher_records AS
            SELECT
                tm.status AS matcher_status,
                COUNT(tm.name) AS matcher_count,
                vfum.file_upload_name 
            FROM
                `tabMatcher` tm
            JOIN `tabSettlement Advice` tsa ON tm.settlement_advice = tsa.name
            JOIN viewFile_Upload_Mail vfum ON tsa.file_upload = vfum.file_upload_name
            GROUP BY 
                vfum.file_upload_name,
                tm.status ;
                """)

    def payment_entry_view(self):
        # Create or replace view 'viewpayment_entry_records'
        frappe.db.sql("""CREATE or REPLACE VIEW viewpayment_entry_records AS
            SELECT
                COUNT(tpe.name) AS pe_count,
                tpe.status AS pe_status,
                SUM(tpe.paid_amount) AS pe_settled,
                SUM(tpe.custom_tds_amount) AS pe_tds,
                SUM(tpe.custom_disallowed_amount) AS pe_disallowance,
                vfum.file_upload_name 
            FROM
                `tabPayment Entry` tpe
            JOIN `tabMatcher` tm ON tpe.custom_sales_invoice = tm.sales_invoice AND tpe.reference_no = tm.bank_transaction
            JOIN `tabSettlement Advice` tsa ON tm.settlement_advice = tsa.name
            JOIN viewFile_Upload_Mail vfum ON tsa.file_upload = vfum.file_upload_name 
            GROUP BY 
                vfum.file_upload_name,
                tpe.status;
                """)
    
    def process(self):
        self.file_upload_mail_view()
        self.file_upload_view()
        self.staging_view()
        self.advice_view()
        self.matcher_view()
        self.payment_entry_view()
        
def execute():
    ViewInstance = ViewCreator()
    ViewInstance.process()