import frappe


class CheckListView():

    def current_year_sales_invoice_report_views(self):
        # Updated viewSales Invoice Current Year - added total_claim_amount to get total_claim_amount in viewSales Invoice Current Year Breakup
        frappe.db.sql("""
        CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW  `viewSales Invoice Current Year` AS
            select
                `tsi`.`name` AS `bill_number`,
                `tsi`.`posting_date` AS `posting_date`,
                `tsi`.`rounded_total` AS `claim_amount`,
                `tsi`.`total` AS `total_claim_amount`,
                `tsi`.`custom_total_tds_amount` AS `tds_amount`,
                `tsi`.`custom_total_settled_amount` AS `settled_amount`,
                `tsi`.`custom_total_disallowance_amount` AS `disallowed_amount`,
                `tsi`.`branch` AS `branch`,
                `tsi`.`entity` AS `entity`,
                `tsi`.`region` AS `region`,
                `tsi`.`customer` AS `customer`,
                `tsi`.`customer_group` AS `customer_group`,
                `tsi`.`outstanding_amount` AS `outstanding_amount`,
                `tsi`.`status` AS `status`,
                `tsi`.`custom_claim_id` AS `custom_claim_id`,
                `tsi`.`branch_type` AS `branch_type`,
                `tsi`.`custom_insurance_name` AS `custom_insurance_name`,
                `tsi`.`custom_patient_name` AS `custom_patient_name`,
                `tsi`.`custom_mrn` AS `mrn`,
                `tsi`.`custom_payer_name` AS `payer_name`,
                `tsi`.`custom_ma_claim_id` AS `ma_claim_id`,
                `tsi`.`custom_mrn` AS `custom_mrn`
            from
                 `tabSales Invoice` `tsi`
            where
                `tsi`.`posting_date` > '2024-03-31'
            union
            select
                `viewSales Invoice Summary`.`name` AS `bill_number`,
                `viewSales Invoice Summary`.`posting_date` AS `posting_date`,
                `viewSales Invoice Summary`.`due_amount` AS `claim_amount`,
                `viewSales Invoice Summary`.`total` AS `total_claim_amount`,
                `viewSales Invoice Summary`.`custom_total_tds_amount` AS `tds_amount`,
                `viewSales Invoice Summary`.`custom_total_settled_amount` AS `settled_amount`,
                `viewSales Invoice Summary`.`custom_total_disallowance_amount` AS `disallowed_amount`,
                `viewSales Invoice Summary`.`branch` AS `branch`,
                `viewSales Invoice Summary`.`entity` AS `entity`,
                `viewSales Invoice Summary`.`region` AS `region`,
                `viewSales Invoice Summary`.`customer` AS `customer`,
                `viewSales Invoice Summary`.`customer_group` AS `customer_group`,
                `viewSales Invoice Summary`.`outstanding_amount` AS `outstanding_amount`,
                `viewSales Invoice Summary`.`status` AS `status`,
                `viewSales Invoice Summary`.`custom_claim_id` AS `custom_claim_id`,
                `viewSales Invoice Summary`.`branch_type` AS `branch_type`,
                `viewSales Invoice Summary`.`custom_insurance_name` AS `custom_insurance_name`,
                `viewSales Invoice Summary`.`custom_patient_name` AS `custom_patient_name`,
                `viewSales Invoice Summary`.`custom_mrn` AS `mrn`,
                `viewSales Invoice Summary`.`custom_payer_name` AS `payer_name`,
                `viewSales Invoice Summary`.`custom_ma_claim_id` AS `ma_claim_id`,
                `viewSales Invoice Summary`.`custom_mrn` AS `custom_mrn`
            from
                 `viewSales Invoice Summary`;   
        """)

        # Updated Added Claim_amount in viewSales Invoice Current Year Breakup to get total_claim_amount in viewcurrent_year_si_checklist
        frappe.db.sql("""
            CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW `viewSales Invoice Current Year Breakup` AS
            select
                `vsicy`.`bill_number` AS `bill_number`,
                `vsicy`.`posting_date` AS `bill_date`,
                `vsicy`.`claim_amount` AS `current_claim_amount`,
                `vsicy`.`total_claim_amount` AS `claim_amount`,
                ifnull(`vss`.`settled`, 0) AS `settled_amount`,
                ifnull(`vss`.`tds`, 0) AS `tds_amount`,
                ifnull(`vss`.`disallowance`, 0) AS `disallowed_amount`,
                `vsicy`.`branch` AS `branch`,
                `vsicy`.`entity` AS `entity`,
                `vsicy`.`region` AS `region`,
                `vsicy`.`customer` AS `customer`,
                `vsicy`.`customer_group` AS `customer_group`,
                `vsicy`.`outstanding_amount` AS `outstanding_amount`,
                `vsicy`.`status` AS `status`,
                `vsicy`.`custom_claim_id` AS `claim_id`,
                `vsicy`.`branch_type` AS `branch_type`,
                `vsicy`.`custom_insurance_name` AS `insurance_name`,
                `vsicy`.`custom_patient_name` AS `patient_name`,
                `vsicy`.`ma_claim_id` AS `ma_claim_id`,
                `vsicy`.`custom_mrn` AS `mrn`
            from
                (`viewSales Invoice Current Year` `vsicy`
            left join `viewSettlement Summary` `vss` on
                (`vsicy`.`bill_number` = `vss`.`bill_number`));
        """)

        # Created viewSales Invoice Current Year Breakup : Total Claim Amount - ( Total Settled + Total TDS + Total Disallowance ) < 9
        frappe.db.sql("""
            CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW  `viewcurrent_year_si_checklist` AS
            select
                `vsicyb`.`bill_number` AS `bill_number`,
                `tfr`.`job` AS `job`,
                `vsicyb`.`claim_amount` AS `claim_amount`,
                `vsicyb`.`outstanding_amount` AS `outstanding_amount`,
                `vsicyb`.`settled_amount` AS `settled_amount`,
                `vsicyb`.`tds_amount` AS `tds_amount`,
                `vsicyb`.`disallowed_amount` AS `disallowed_amount`,
                `vsicyb`.`claim_amount` - (`vsicyb`.`settled_amount` + `vsicyb`.`tds_amount` + `vsicyb`.`disallowed_amount` + `vsicyb`.`outstanding_amount`) AS `diff`
            from
                ((`tabFile Records` `tfr`
            join `tabPayment Entry` `tpe` on
                (`tpe`.`name` = `tfr`.`record`))
            join `viewSales Invoice Current Year Breakup` `vsicyb` on
                (`vsicyb`.`bill_number` = `tpe`.`custom_sales_invoice`));
        """)

        # Created viewcumulative_current_year_sales_invoice
        # : Total TDS/Total Disallowance/Total Settled = Total of TDS/Disallowance/Settled

        frappe.db.sql("""
            CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW `viewcumulative_current_year_sales_invoice` AS
            select
                `t1`.`Bill Number` AS `Bill Number`,
                `t1`.`Sum Settled Amount` AS `Sum Settled Amount`,
                `t1`.`Sum Disallowance Amount` AS `Sum Disallowance Amount`,
                `t1`.`Sum TDS Amount` AS `Sum TDS Amount`,
                `t2`.`Total Settled Amount` AS `Total Settled Amount`,
                `t2`.`Total TDS Amount` AS `Total TDS Amount`,
                `t2`.`Total Disallowance Amount` AS `Total Disallowance Amount`
            from
                ((
                select
                    `vsirwrn`.`Bill Number` AS `Bill Number`,
                    sum(`vsirwrn`.`Settled Amount`) AS `Sum Settled Amount`,
                    sum(`vsirwrn`.`Disallowed Amount`) AS `Sum Disallowance Amount`,
                    sum(`vsirwrn`.`TDS Amount`) AS `Sum TDS Amount`
                from
                    `viewSales Invoice Report 24-25 with Row Number` `vsirwrn`
                group by
                    `vsirwrn`.`Bill Number`) `t1`
            join (
                select
                    case
                        when `vsirwrn`.`row_count` = 1 then `vsirwrn`.`Bill Number`
                        else 0
                    end AS `Bill Number`,
                    `vsirwrn`.`Total Settled Amount` AS `Total Settled Amount`,
                    `vsirwrn`.`Total TDS Amount` AS `Total TDS Amount`,
                    `vsirwrn`.`Total Disallowance Amount` AS `Total Disallowance Amount`
                from
                   `viewSales Invoice Report 24-25 with Row Number` `vsirwrn`) `t2` on
                (`t1`.`Bill Number` = `t2`.`Bill Number`));
        """)

        # Created viewcumulative_current_year_sales_invoice_with_job view it contains cumulative values with job ID
        frappe.db.sql("""
        CREATE OR REPLACE
        ALGORITHM = UNDEFINED VIEW `viewcumulative_current_year_sales_invoice_with_job` AS
        select
            `tfr`.`job` AS `job`,
            sum(`vcysi`.`Sum Settled Amount`) AS `Sum Settled Amount`,
            sum(`vcysi`.`Sum Disallowance Amount`) AS `Sum Disallowance Amount`,
            sum(`vcysi`.`Sum TDS Amount`) AS `Sum TDS Amount`,
            sum(`vcysi`.`Total Settled Amount`) AS `Total Settled Amount`,
            sum(`vcysi`.`Total TDS Amount`) AS `Total TDS Amount`,
            sum(`vcysi`.`Total Disallowance Amount`) AS `Total Disallowance Amount`
        from
            ((`tabFile Records` `tfr`
        join`tabPayment Entry` `tpe` on
            (`tpe`.`name` = `tfr`.`record`))
        join  `viewcumulative_current_year_sales_invoice` `vcysi` on
            (`tpe`.`custom_sales_invoice` = `vcysi`.`Bill Number`))
        group by
            `tfr`.`job`;
        """)

    def current_year_bank_transaction_report_views(self):
        # Created viewcumulative_bank_report_checklist to get the cumulative values in current year bank report

        frappe.db.sql("""
            CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW `viewcumulative_bank_report_checklist` AS
            select
                `t1`.`UTR_Number` AS `UTR_Number`,
                `t1`.`Total_Allocated` AS `Total_Allocated`,
                `t2`.`Current_Allocated_Amount` AS `Current_Allocated_Amount`,
                `t1`.`Total_Allocated` - `t2`.`Current_Allocated_Amount` AS `DIFF`
            from
                ((
                select
                    `viewSorted Current Brank Transaction`.`UTR_Number` AS `UTR_Number`,
                    sum(`viewSorted Current Brank Transaction`.`Allocated_Amount(Payment_Entries)`) AS `Total_Allocated`
                from
                    `viewSorted Current Brank Transaction`
                group by
                    `viewSorted Current Brank Transaction`.`UTR_Number`
                having
                    `Total_Allocated` is not null) `t1`
            left join (
                select
                    `vscbt`.`UTR_Number` AS `UTR_Number`,
                    case
                        when `vscbt`.`row_count` = 1 then `vscbt`.`Current_Allocated_Amount`
                        else NULL
                    end AS `Current_Allocated_Amount`
                from
                   `viewSorted Current Brank Transaction` `vscbt`
                having
                    `Current_Allocated_Amount` is not null
                    and `Current_Allocated_Amount` <> 0) `t2` on
                (`t1`.`UTR_Number` = `t2`.`UTR_Number`));

        """)

        # Created viewcurrent_bank_report_checklist - to get the difference of Total Deposit - (Total Allocated + Total Un-allocated) < 9
        frappe.db.sql("""
            CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW  `viewcurrent_bank_report_checklist` AS
            select
                `tfr`.`job` AS `job`,
                case when `vscbt`.`row_count` = 1 then `vscbt`.`UTR_Number` else NULL end AS `UTR`,
                case when `vscbt`.`row_count` = 1 then `vscbt`.`Current_Allocated_Amount`else NULL end AS `Allocated Amount`,
                case when `vscbt`.`row_count` = 1 then `vscbt`.`Current_UnAllocated` else NULL end AS `Un-Allocated Amount`,
                case when `vscbt`.`row_count` = 1 then `vscbt`.`Current_Deposit` else NULL end AS `Deposit`,
                case when `vscbt`.`row_count` = 1 then `vscbt`.`Current_Deposit` - (`vscbt`.`Current_Allocated_Amount` + `vscbt`.`Current_UnAllocated`) else NULL end AS `diff`
            from
                ((`tabFile Records` `tfr`
            join  `tabPayment Entry` `tpe` on
                (`tpe`.`name` = `tfr`.`record`))
            join  `viewSorted Current Brank Transaction` `vscbt` on
                (`vscbt`.`UTR_Number` = `tpe`.`reference_no`))
            having
                `UTR` is not null
            order by
                `vscbt`.`row_count`;  
        """)

    def process(self):
        self.current_year_sales_invoice_report_views()
        self.current_year_bank_transaction_report_views()

def execute():
    obj = CheckListView()
    obj.process()
