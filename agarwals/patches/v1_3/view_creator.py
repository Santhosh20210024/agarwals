import frappe

class ViewCreator:
    def create_file_upload_mail_view(self):
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

    def create_file_upload_view(self):
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

    def create_staging_view(self):
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
                vfum.file_upload_name,
            tsas.error_code,
            tsas.status ;
            """)

    def create_advice_view(self):
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
                vfum.file_upload_name ,
                tsa.status;
                """)

    def create_matcher_view(self):
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

    def create_payment_entry_view(self):
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
        
    def create_collection_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `Collection` AS
        select
            `pe`.`paid_amount` AS `Collection`,
            `pe`.`custom_due_date` AS `Date`,
            `pe`.`region` AS `Region`,
            `pe`.`entity` AS `Entity`,
            ucase(`cg`.`customer_group`) AS `Category`
        from
            (`tabPayment Entry` `pe`
        join `tabCustomer` `cg`)
        where
            `pe`.`title` = `cg`.`name`
            and `pe`.`status` <> 'Cancelled'
        union all
        select
            `be`.`unallocated_amount` AS `Collection`,
            `be`.`date` AS `Date`,
            `be`.`custom_region` AS `Region`,
            `be`.`custom_entity` AS `Entity`,
            ucase(`be`.`custom_party_group`) AS `Category`
        from
            `tabBank Transaction` `be`
        where
            `be`.`status` <> 'Cancelled';
            """)
        
    def create_current_bank_transaction_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `current_bank_transaction` AS
            select
                `tbt`.`custom_entity` AS `Entity`,
                `tbt`.`custom_region` AS `Region`,
                `tbt`.`custom_party_group` AS `Party_Group`,
                `tbt`.`party` AS `Insurance`,
                `tbt`.`name` AS `UTR_Number`,
                `tbt`.`date` AS `UTR_Date`,
                coalesce(`table1`.`Current_Allocated_Amount`, 0) AS `Current_Allocated_Amount`,
                `tbt`.`unallocated_amount` AS `Current_UnAllocated`,
                coalesce(`table2`.`current_deposit`, `tbt`.`deposit`) AS `Current_Deposit`,
                `tbt`.`custom_branch_type` AS `Branch_Type`,
                `tbt`.`status` AS `Status`,
                `tbt`.`bank_account` AS `Bank_Account`,
                `tbt`.`custom_ns_ledger_code` AS `NS_Ledger_Code`,
                `tbt`.`description` AS `Description`,
                `tbt`.`reference_number` AS `Reference_Number`,
                `tbt`.`custom_internal_id` AS `Internal_Id`,
                `tbt`.`custom_based_on` AS `Based_On`,
                `btp`.`allocated_amount` AS `Allocated_Amount(Payment_Entries)`,
                `btp`.`payment_document` AS `Payment_Document(Payment_Entries)`,
                `btp`.`payment_entry` AS `Payment_Entry(Payment_Entries)`,
                `btp`.`custom_bill_region` AS `Bill_Region(Payment_Entries)`,
                `btp`.`custom_creation_date` AS `Creation_Date(Payment_Entries)`,
                `btp`.`custom_posting_date` AS `Posting_Date(Payment_Entries)`,
                `btp`.`custom_bill_date` AS `Bill_Date(Payment_Entries)`,
                `btp`.`custom_bill_branch` AS `Bill_Branch(Payment_Entries)`,
                `btp`.`custom_bill_entity` AS `Bill_Entity(Payment_Entries)`,
                `btp`.`custom_bill_branch_type` AS `Bill_Branch_Type(Payment_Entries)`
            from
                (((`tabBank Transaction` `tbt`
            left join (
                select
                    `tpe`.`reference_no` AS `UTR_Number`,
                    sum(`tpe`.`paid_amount`) AS `Current_Allocated_Amount`
                from
                    `tabPayment Entry` `tpe`
                where
                    `tpe`.`status` <> 'Cancelled'
                    and cast(`tpe`.`posting_date` as date) >= (
                    select
                        `tfy`.`year_start_date`
                    from
                        `tabFiscal Year` `tfy`
                    where
                        curdate() >= `tfy`.`year_start_date`
                        and curdate() <= `tfy`.`year_end_date`)
                group by
                    `tpe`.`reference_no`) `table1` on
                (`tbt`.`name` = `table1`.`UTR_Number`))
            left join (
                select
                    `tyd`.`parent` AS `utr_number`,
                    `tyd`.`due_amount` AS `current_deposit`,
                    `tyd`.`fiscal_year` AS `fiscal_year`
                from
                    `tabYearly Due` `tyd`
                where
                    `tyd`.`fiscal_year` = (
                    select
                        `tfy2`.`name`
                    from
                        `tabFiscal Year` `tfy2`
                    where
                        `tfy2`.`year_start_date` <= (
                        select
                            (
                            select
                                `tfy3`.`year_start_date`
                            from
                                `tabFiscal Year` `tfy3`
                            where
                                curdate() >= `tfy3`.`year_start_date`
                                and curdate() <= `tfy3`.`year_end_date`) - interval 1 day)
                        and `tfy2`.`year_end_date` >= (
                        select
                            (
                            select
                                `tfy3`.`year_start_date`
                            from
                                `tabFiscal Year` `tfy3`
                            where
                                curdate() >= `tfy3`.`year_start_date`
                                and curdate() <= `tfy3`.`year_end_date`) - interval 1 day))) `table2` on
                (`table2`.`utr_number` = `tbt`.`name`))
            left join (
                select
                    `tabBank Transaction Payments`.`name` AS `name`,
                    `tabBank Transaction Payments`.`creation` AS `creation`,
                    `tabBank Transaction Payments`.`modified` AS `modified`,
                    `tabBank Transaction Payments`.`modified_by` AS `modified_by`,
                    `tabBank Transaction Payments`.`owner` AS `owner`,
                    `tabBank Transaction Payments`.`docstatus` AS `docstatus`,
                    `tabBank Transaction Payments`.`idx` AS `idx`,
                    `tabBank Transaction Payments`.`payment_document` AS `payment_document`,
                    `tabBank Transaction Payments`.`payment_entry` AS `payment_entry`,
                    `tabBank Transaction Payments`.`allocated_amount` AS `allocated_amount`,
                    `tabBank Transaction Payments`.`clearance_date` AS `clearance_date`,
                    `tabBank Transaction Payments`.`parent` AS `parent`,
                    `tabBank Transaction Payments`.`parentfield` AS `parentfield`,
                    `tabBank Transaction Payments`.`parenttype` AS `parenttype`,
                    `tabBank Transaction Payments`.`custom_bill_region` AS `custom_bill_region`,
                    `tabBank Transaction Payments`.`custom_bill_date` AS `custom_bill_date`,
                    `tabBank Transaction Payments`.`custom_bill_branch` AS `custom_bill_branch`,
                    `tabBank Transaction Payments`.`custom_bill_entity` AS `custom_bill_entity`,
                    `tabBank Transaction Payments`.`custom_bill_category` AS `custom_bill_category`,
                    `tabBank Transaction Payments`.`bill_date` AS `bill_date`,
                    `tabBank Transaction Payments`.`bill_region` AS `bill_region`,
                    `tabBank Transaction Payments`.`bill_entity` AS `bill_entity`,
                    `tabBank Transaction Payments`.`bill_branch` AS `bill_branch`,
                    `tabBank Transaction Payments`.`bill_branch_type` AS `bill_branch_type`,
                    `tabBank Transaction Payments`.`custom_bill_branch_type` AS `custom_bill_branch_type`,
                    `tabBank Transaction Payments`.`custom_posting_date` AS `custom_posting_date`,
                    `tabBank Transaction Payments`.`custom_creation_date` AS `custom_creation_date`
                from
                    `tabBank Transaction Payments`
                where
                    `tabBank Transaction Payments`.`custom_posting_date` > '2024-03-31') `btp` on
                (`btp`.`parent` = `tbt`.`name`))
            where
                `tbt`.`status` <> 'Cancelled';
            """)
        
    def create_current_sales_invoice_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `current_sales_invoice` AS
            select
                `jv`.`name` AS `Bill No`,
                `jv`.`posting_date` AS `Bill Date`,
                `tyd`.`due_amount` AS `Current Claim Amount`,
                `pen`.`pe_paid` AS `Paid Amount`,
                `pen`.`pe_tds` AS `TDS Amount`,
                `pen`.`pe_dis` AS `Disallowance Amount`,
                `jv`.`jv` AS `JV Amount`,
                `jv`.`status` AS `Bill Status`
            from
                (((
                select
                    `tsi`.`name` AS `name`,
                    `tsi`.`creation` AS `creation`,
                    `tsi`.`modified` AS `modified`,
                    `tsi`.`modified_by` AS `modified_by`,
                    `tsi`.`owner` AS `owner`,
                    `tsi`.`docstatus` AS `docstatus`,
                    `tsi`.`idx` AS `idx`,
                    `tsi`.`title` AS `title`,
                    `tsi`.`bill_no` AS `bill_no`,
                    `tsi`.`naming_series` AS `naming_series`,
                    `tsi`.`customer` AS `customer`,
                    `tsi`.`customer_name` AS `customer_name`,
                    `tsi`.`tax_id` AS `tax_id`,
                    `tsi`.`company` AS `company`,
                    `tsi`.`company_tax_id` AS `company_tax_id`,
                    `tsi`.`posting_date` AS `posting_date`,
                    `tsi`.`posting_time` AS `posting_time`,
                    `tsi`.`set_posting_time` AS `set_posting_time`,
                    `tsi`.`due_date` AS `due_date`,
                    `tsi`.`is_pos` AS `is_pos`,
                    `tsi`.`pos_profile` AS `pos_profile`,
                    `tsi`.`is_consolidated` AS `is_consolidated`,
                    `tsi`.`is_return` AS `is_return`,
                    `tsi`.`return_against` AS `return_against`,
                    `tsi`.`update_billed_amount_in_sales_order` AS `update_billed_amount_in_sales_order`,
                    `tsi`.`is_debit_note` AS `is_debit_note`,
                    `tsi`.`amended_from` AS `amended_from`,
                    `tsi`.`cost_center` AS `cost_center`,
                    `tsi`.`project` AS `project`,
                    `tsi`.`currency` AS `currency`,
                    `tsi`.`conversion_rate` AS `conversion_rate`,
                    `tsi`.`selling_price_list` AS `selling_price_list`,
                    `tsi`.`price_list_currency` AS `price_list_currency`,
                    `tsi`.`plc_conversion_rate` AS `plc_conversion_rate`,
                    `tsi`.`ignore_pricing_rule` AS `ignore_pricing_rule`,
                    `tsi`.`scan_barcode` AS `scan_barcode`,
                    `tsi`.`update_stock` AS `update_stock`,
                    `tsi`.`set_warehouse` AS `set_warehouse`,
                    `tsi`.`set_target_warehouse` AS `set_target_warehouse`,
                    `tsi`.`total_qty` AS `total_qty`,
                    `tsi`.`total_net_weight` AS `total_net_weight`,
                    `tsi`.`base_total` AS `base_total`,
                    `tsi`.`base_net_total` AS `base_net_total`,
                    `tsi`.`total` AS `total`,
                    `tsi`.`net_total` AS `net_total`,
                    `tsi`.`tax_category` AS `tax_category`,
                    `tsi`.`taxes_and_charges` AS `taxes_and_charges`,
                    `tsi`.`shipping_rule` AS `shipping_rule`,
                    `tsi`.`incoterm` AS `incoterm`,
                    `tsi`.`named_place` AS `named_place`,
                    `tsi`.`base_total_taxes_and_charges` AS `base_total_taxes_and_charges`,
                    `tsi`.`total_taxes_and_charges` AS `total_taxes_and_charges`,
                    `tsi`.`base_grand_total` AS `base_grand_total`,
                    `tsi`.`base_rounding_adjustment` AS `base_rounding_adjustment`,
                    `tsi`.`base_rounded_total` AS `base_rounded_total`,
                    `tsi`.`base_in_words` AS `base_in_words`,
                    `tsi`.`grand_total` AS `grand_total`,
                    `tsi`.`rounding_adjustment` AS `rounding_adjustment`,
                    `tsi`.`use_company_roundoff_cost_center` AS `use_company_roundoff_cost_center`,
                    `tsi`.`rounded_total` AS `rounded_total`,
                    `tsi`.`in_words` AS `in_words`,
                    `tsi`.`total_advance` AS `total_advance`,
                    `tsi`.`outstanding_amount` AS `outstanding_amount`,
                    `tsi`.`disable_rounded_total` AS `disable_rounded_total`,
                    `tsi`.`apply_discount_on` AS `apply_discount_on`,
                    `tsi`.`base_discount_amount` AS `base_discount_amount`,
                    `tsi`.`is_cash_or_non_trade_discount` AS `is_cash_or_non_trade_discount`,
                    `tsi`.`additional_discount_account` AS `additional_discount_account`,
                    `tsi`.`additional_discount_percentage` AS `additional_discount_percentage`,
                    `tsi`.`discount_amount` AS `discount_amount`,
                    `tsi`.`other_charges_calculation` AS `other_charges_calculation`,
                    `tsi`.`total_billing_hours` AS `total_billing_hours`,
                    `tsi`.`total_billing_amount` AS `total_billing_amount`,
                    `tsi`.`cash_bank_account` AS `cash_bank_account`,
                    `tsi`.`base_paid_amount` AS `base_paid_amount`,
                    `tsi`.`paid_amount` AS `paid_amount`,
                    `tsi`.`base_change_amount` AS `base_change_amount`,
                    `tsi`.`change_amount` AS `change_amount`,
                    `tsi`.`account_for_change_amount` AS `account_for_change_amount`,
                    `tsi`.`allocate_advances_automatically` AS `allocate_advances_automatically`,
                    `tsi`.`only_include_allocated_payments` AS `only_include_allocated_payments`,
                    `tsi`.`write_off_amount` AS `write_off_amount`,
                    `tsi`.`base_write_off_amount` AS `base_write_off_amount`,
                    `tsi`.`write_off_outstanding_amount_automatically` AS `write_off_outstanding_amount_automatically`,
                    `tsi`.`write_off_account` AS `write_off_account`,
                    `tsi`.`write_off_cost_center` AS `write_off_cost_center`,
                    `tsi`.`redeem_loyalty_points` AS `redeem_loyalty_points`,
                    `tsi`.`loyalty_points` AS `loyalty_points`,
                    `tsi`.`loyalty_amount` AS `loyalty_amount`,
                    `tsi`.`loyalty_program` AS `loyalty_program`,
                    `tsi`.`loyalty_redemption_account` AS `loyalty_redemption_account`,
                    `tsi`.`loyalty_redemption_cost_center` AS `loyalty_redemption_cost_center`,
                    `tsi`.`customer_address` AS `customer_address`,
                    `tsi`.`address_display` AS `address_display`,
                    `tsi`.`contact_person` AS `contact_person`,
                    `tsi`.`contact_display` AS `contact_display`,
                    `tsi`.`contact_mobile` AS `contact_mobile`,
                    `tsi`.`contact_email` AS `contact_email`,
                    `tsi`.`territory` AS `territory`,
                    `tsi`.`shipping_address_name` AS `shipping_address_name`,
                    `tsi`.`shipping_address` AS `shipping_address`,
                    `tsi`.`dispatch_address_name` AS `dispatch_address_name`,
                    `tsi`.`dispatch_address` AS `dispatch_address`,
                    `tsi`.`company_address` AS `company_address`,
                    `tsi`.`company_address_display` AS `company_address_display`,
                    `tsi`.`ignore_default_payment_terms_template` AS `ignore_default_payment_terms_template`,
                    `tsi`.`payment_terms_template` AS `payment_terms_template`,
                    `tsi`.`tc_name` AS `tc_name`,
                    `tsi`.`terms` AS `terms`,
                    `tsi`.`po_no` AS `po_no`,
                    `tsi`.`po_date` AS `po_date`,
                    `tsi`.`debit_to` AS `debit_to`,
                    `tsi`.`party_account_currency` AS `party_account_currency`,
                    `tsi`.`is_opening` AS `is_opening`,
                    `tsi`.`unrealized_profit_loss_account` AS `unrealized_profit_loss_account`,
                    `tsi`.`against_income_account` AS `against_income_account`,
                    `tsi`.`sales_partner` AS `sales_partner`,
                    `tsi`.`amount_eligible_for_commission` AS `amount_eligible_for_commission`,
                    `tsi`.`commission_rate` AS `commission_rate`,
                    `tsi`.`total_commission` AS `total_commission`,
                    `tsi`.`letter_head` AS `letter_head`,
                    `tsi`.`group_same_items` AS `group_same_items`,
                    `tsi`.`select_print_heading` AS `select_print_heading`,
                    `tsi`.`language` AS `language`,
                    `tsi`.`from_date` AS `from_date`,
                    `tsi`.`auto_repeat` AS `auto_repeat`,
                    `tsi`.`to_date` AS `to_date`,
                    `tsi`.`status` AS `status`,
                    `tsi`.`inter_company_invoice_reference` AS `inter_company_invoice_reference`,
                    `tsi`.`campaign` AS `campaign`,
                    `tsi`.`represents_company` AS `represents_company`,
                    `tsi`.`source` AS `source`,
                    `tsi`.`customer_group` AS `customer_group`,
                    `tsi`.`is_internal_customer` AS `is_internal_customer`,
                    `tsi`.`is_discounted` AS `is_discounted`,
                    `tsi`.`remarks` AS `remarks`,
                    `tsi`.`repost_required` AS `repost_required`,
                    `tsi`.`_user_tags` AS `_user_tags`,
                    `tsi`.`_comments` AS `_comments`,
                    `tsi`.`_assign` AS `_assign`,
                    `tsi`.`_liked_by` AS `_liked_by`,
                    `tsi`.`_seen` AS `_seen`,
                    `tsi`.`custom_bill_no` AS `custom_bill_no`,
                    `tsi`.`region` AS `region`,
                    `tsi`.`branch` AS `branch`,
                    `tsi`.`branch_type` AS `branch_type`,
                    `tsi`.`entity` AS `entity`,
                    `tsi`.`custom_insurance_name` AS `custom_insurance_name`,
                    `tsi`.`update_billed_amount_in_delivery_note` AS `update_billed_amount_in_delivery_note`,
                    `tsi`.`dont_create_loyalty_points` AS `dont_create_loyalty_points`,
                    `tsi`.`custom_mrn` AS `custom_mrn`,
                    `tsi`.`custom_claim_id` AS `custom_claim_id`,
                    `tsi`.`total_outstanding_amount` AS `total_outstanding_amount`,
                    `tsi`.`custom_ma_claim_id` AS `custom_ma_claim_id`,
                    `tsi`.`custom_patient_name` AS `custom_patient_name`,
                    `tsi`.`custom_payer_name` AS `custom_payer_name`,
                    `tsi`.`sales_status1` AS `sales_status1`,
                    `tsi`.`custom_year` AS `custom_year`,
                    `tsi`.`custom_month` AS `custom_month`,
                    `tsi`.`update_outstanding_for_self` AS `update_outstanding_for_self`,
                    `tsi`.`custom_tds_amount` AS `custom_tds_amount`,
                    `tsi`.`custom_total_tds_amount` AS `custom_total_tds_amount`,
                    `tsi`.`custom_total_disallowance_amount` AS `custom_total_disallowance_amount`,
                    `tsi`.`custom_total_settled_amount` AS `custom_total_settled_amount`,
                    `tsi`.`custom_total_writeoff_amount` AS `custom_total_writeoff_amount`,
                    `tsi`.`custom_total_amount_number_card` AS `custom_total_amount_number_card`,
                    `tsi`.`custom_file_upload` AS `custom_file_upload`,
                    `tsi`.`custom_transform` AS `custom_transform`,
                    `tsi`.`custom_index` AS `custom_index`,
                    `je`.`rn` AS `rn`,
                    `je`.`je_posting_date` AS `je_posting_date`,
                    `je`.`jv` AS `jv`
                from
                    (`tabSales Invoice` `tsi`
                left join (
                    select
                        `tjea`.`reference_name` AS `rn`,
                        `tje`.`posting_date` AS `je_posting_date`,
                        sum(`tjea`.`credit`) AS `jv`
                    from
                        ((`tabJournal Entry Account` `tjea`
                    left join `tabJournal Entry` `tje` on
                        (`tje`.`name` = `tjea`.`parent`))
                    join (
                        select
                            `tfy`.`year_start_date` AS `ysd`,
                            `tfy`.`year_end_date` AS `yed`
                        from
                            `tabFiscal Year` `tfy`
                        where
                            curdate() between `tfy`.`year_start_date` and `tfy`.`year_end_date`) `fy` on
                        (cast(`tje`.`posting_date` as date) between cast(`fy`.`ysd` as date) and cast(`fy`.`yed` as date)))
                    group by
                        `tjea`.`reference_name`) `je` on
                    (`tsi`.`name` = `je`.`rn`))
                where
                    `tsi`.`status` <> 'Cancelled'
                group by
                    `tsi`.`name`) `jv`
            join (
                select
                    `tsi`.`name` AS `name`,
                    `tsi`.`creation` AS `creation`,
                    `tsi`.`modified` AS `modified`,
                    `tsi`.`modified_by` AS `modified_by`,
                    `tsi`.`owner` AS `owner`,
                    `tsi`.`docstatus` AS `docstatus`,
                    `tsi`.`idx` AS `idx`,
                    `tsi`.`title` AS `title`,
                    `tsi`.`bill_no` AS `bill_no`,
                    `tsi`.`naming_series` AS `naming_series`,
                    `tsi`.`customer` AS `customer`,
                    `tsi`.`customer_name` AS `customer_name`,
                    `tsi`.`tax_id` AS `tax_id`,
                    `tsi`.`company` AS `company`,
                    `tsi`.`company_tax_id` AS `company_tax_id`,
                    `tsi`.`posting_date` AS `posting_date`,
                    `tsi`.`posting_time` AS `posting_time`,
                    `tsi`.`set_posting_time` AS `set_posting_time`,
                    `tsi`.`due_date` AS `due_date`,
                    `tsi`.`is_pos` AS `is_pos`,
                    `tsi`.`pos_profile` AS `pos_profile`,
                    `tsi`.`is_consolidated` AS `is_consolidated`,
                    `tsi`.`is_return` AS `is_return`,
                    `tsi`.`return_against` AS `return_against`,
                    `tsi`.`update_billed_amount_in_sales_order` AS `update_billed_amount_in_sales_order`,
                    `tsi`.`is_debit_note` AS `is_debit_note`,
                    `tsi`.`amended_from` AS `amended_from`,
                    `tsi`.`cost_center` AS `cost_center`,
                    `tsi`.`project` AS `project`,
                    `tsi`.`currency` AS `currency`,
                    `tsi`.`conversion_rate` AS `conversion_rate`,
                    `tsi`.`selling_price_list` AS `selling_price_list`,
                    `tsi`.`price_list_currency` AS `price_list_currency`,
                    `tsi`.`plc_conversion_rate` AS `plc_conversion_rate`,
                    `tsi`.`ignore_pricing_rule` AS `ignore_pricing_rule`,
                    `tsi`.`scan_barcode` AS `scan_barcode`,
                    `tsi`.`update_stock` AS `update_stock`,
                    `tsi`.`set_warehouse` AS `set_warehouse`,
                    `tsi`.`set_target_warehouse` AS `set_target_warehouse`,
                    `tsi`.`total_qty` AS `total_qty`,
                    `tsi`.`total_net_weight` AS `total_net_weight`,
                    `tsi`.`base_total` AS `base_total`,
                    `tsi`.`base_net_total` AS `base_net_total`,
                    `tsi`.`total` AS `total`,
                    `tsi`.`net_total` AS `net_total`,
                    `tsi`.`tax_category` AS `tax_category`,
                    `tsi`.`taxes_and_charges` AS `taxes_and_charges`,
                    `tsi`.`shipping_rule` AS `shipping_rule`,
                    `tsi`.`incoterm` AS `incoterm`,
                    `tsi`.`named_place` AS `named_place`,
                    `tsi`.`base_total_taxes_and_charges` AS `base_total_taxes_and_charges`,
                    `tsi`.`total_taxes_and_charges` AS `total_taxes_and_charges`,
                    `tsi`.`base_grand_total` AS `base_grand_total`,
                    `tsi`.`base_rounding_adjustment` AS `base_rounding_adjustment`,
                    `tsi`.`base_rounded_total` AS `base_rounded_total`,
                    `tsi`.`base_in_words` AS `base_in_words`,
                    `tsi`.`grand_total` AS `grand_total`,
                    `tsi`.`rounding_adjustment` AS `rounding_adjustment`,
                    `tsi`.`use_company_roundoff_cost_center` AS `use_company_roundoff_cost_center`,
                    `tsi`.`rounded_total` AS `rounded_total`,
                    `tsi`.`in_words` AS `in_words`,
                    `tsi`.`total_advance` AS `total_advance`,
                    `tsi`.`outstanding_amount` AS `outstanding_amount`,
                    `tsi`.`disable_rounded_total` AS `disable_rounded_total`,
                    `tsi`.`apply_discount_on` AS `apply_discount_on`,
                    `tsi`.`base_discount_amount` AS `base_discount_amount`,
                    `tsi`.`is_cash_or_non_trade_discount` AS `is_cash_or_non_trade_discount`,
                    `tsi`.`additional_discount_account` AS `additional_discount_account`,
                    `tsi`.`additional_discount_percentage` AS `additional_discount_percentage`,
                    `tsi`.`discount_amount` AS `discount_amount`,
                    `tsi`.`other_charges_calculation` AS `other_charges_calculation`,
                    `tsi`.`total_billing_hours` AS `total_billing_hours`,
                    `tsi`.`total_billing_amount` AS `total_billing_amount`,
                    `tsi`.`cash_bank_account` AS `cash_bank_account`,
                    `tsi`.`base_paid_amount` AS `base_paid_amount`,
                    `tsi`.`paid_amount` AS `paid_amount`,
                    `tsi`.`base_change_amount` AS `base_change_amount`,
                    `tsi`.`change_amount` AS `change_amount`,
                    `tsi`.`account_for_change_amount` AS `account_for_change_amount`,
                    `tsi`.`allocate_advances_automatically` AS `allocate_advances_automatically`,
                    `tsi`.`only_include_allocated_payments` AS `only_include_allocated_payments`,
                    `tsi`.`write_off_amount` AS `write_off_amount`,
                    `tsi`.`base_write_off_amount` AS `base_write_off_amount`,
                    `tsi`.`write_off_outstanding_amount_automatically` AS `write_off_outstanding_amount_automatically`,
                    `tsi`.`write_off_account` AS `write_off_account`,
                    `tsi`.`write_off_cost_center` AS `write_off_cost_center`,
                    `tsi`.`redeem_loyalty_points` AS `redeem_loyalty_points`,
                    `tsi`.`loyalty_points` AS `loyalty_points`,
                    `tsi`.`loyalty_amount` AS `loyalty_amount`,
                    `tsi`.`loyalty_program` AS `loyalty_program`,
                    `tsi`.`loyalty_redemption_account` AS `loyalty_redemption_account`,
                    `tsi`.`loyalty_redemption_cost_center` AS `loyalty_redemption_cost_center`,
                    `tsi`.`customer_address` AS `customer_address`,
                    `tsi`.`address_display` AS `address_display`,
                    `tsi`.`contact_person` AS `contact_person`,
                    `tsi`.`contact_display` AS `contact_display`,
                    `tsi`.`contact_mobile` AS `contact_mobile`,
                    `tsi`.`contact_email` AS `contact_email`,
                    `tsi`.`territory` AS `territory`,
                    `tsi`.`shipping_address_name` AS `shipping_address_name`,
                    `tsi`.`shipping_address` AS `shipping_address`,
                    `tsi`.`dispatch_address_name` AS `dispatch_address_name`,
                    `tsi`.`dispatch_address` AS `dispatch_address`,
                    `tsi`.`company_address` AS `company_address`,
                    `tsi`.`company_address_display` AS `company_address_display`,
                    `tsi`.`ignore_default_payment_terms_template` AS `ignore_default_payment_terms_template`,
                    `tsi`.`payment_terms_template` AS `payment_terms_template`,
                    `tsi`.`tc_name` AS `tc_name`,
                    `tsi`.`terms` AS `terms`,
                    `tsi`.`po_no` AS `po_no`,
                    `tsi`.`po_date` AS `po_date`,
                    `tsi`.`debit_to` AS `debit_to`,
                    `tsi`.`party_account_currency` AS `party_account_currency`,
                    `tsi`.`is_opening` AS `is_opening`,
                    `tsi`.`unrealized_profit_loss_account` AS `unrealized_profit_loss_account`,
                    `tsi`.`against_income_account` AS `against_income_account`,
                    `tsi`.`sales_partner` AS `sales_partner`,
                    `tsi`.`amount_eligible_for_commission` AS `amount_eligible_for_commission`,
                    `tsi`.`commission_rate` AS `commission_rate`,
                    `tsi`.`total_commission` AS `total_commission`,
                    `tsi`.`letter_head` AS `letter_head`,
                    `tsi`.`group_same_items` AS `group_same_items`,
                    `tsi`.`select_print_heading` AS `select_print_heading`,
                    `tsi`.`language` AS `language`,
                    `tsi`.`from_date` AS `from_date`,
                    `tsi`.`auto_repeat` AS `auto_repeat`,
                    `tsi`.`to_date` AS `to_date`,
                    `tsi`.`status` AS `status`,
                    `tsi`.`inter_company_invoice_reference` AS `inter_company_invoice_reference`,
                    `tsi`.`campaign` AS `campaign`,
                    `tsi`.`represents_company` AS `represents_company`,
                    `tsi`.`source` AS `source`,
                    `tsi`.`customer_group` AS `customer_group`,
                    `tsi`.`is_internal_customer` AS `is_internal_customer`,
                    `tsi`.`is_discounted` AS `is_discounted`,
                    `tsi`.`remarks` AS `remarks`,
                    `tsi`.`repost_required` AS `repost_required`,
                    `tsi`.`_user_tags` AS `_user_tags`,
                    `tsi`.`_comments` AS `_comments`,
                    `tsi`.`_assign` AS `_assign`,
                    `tsi`.`_liked_by` AS `_liked_by`,
                    `tsi`.`_seen` AS `_seen`,
                    `tsi`.`custom_bill_no` AS `custom_bill_no`,
                    `tsi`.`region` AS `region`,
                    `tsi`.`branch` AS `branch`,
                    `tsi`.`branch_type` AS `branch_type`,
                    `tsi`.`entity` AS `entity`,
                    `tsi`.`custom_insurance_name` AS `custom_insurance_name`,
                    `tsi`.`update_billed_amount_in_delivery_note` AS `update_billed_amount_in_delivery_note`,
                    `tsi`.`dont_create_loyalty_points` AS `dont_create_loyalty_points`,
                    `tsi`.`custom_mrn` AS `custom_mrn`,
                    `tsi`.`custom_claim_id` AS `custom_claim_id`,
                    `tsi`.`total_outstanding_amount` AS `total_outstanding_amount`,
                    `tsi`.`custom_ma_claim_id` AS `custom_ma_claim_id`,
                    `tsi`.`custom_patient_name` AS `custom_patient_name`,
                    `tsi`.`custom_payer_name` AS `custom_payer_name`,
                    `tsi`.`sales_status1` AS `sales_status1`,
                    `tsi`.`custom_year` AS `custom_year`,
                    `tsi`.`custom_month` AS `custom_month`,
                    `tsi`.`update_outstanding_for_self` AS `update_outstanding_for_self`,
                    `tsi`.`custom_tds_amount` AS `custom_tds_amount`,
                    `tsi`.`custom_total_tds_amount` AS `custom_total_tds_amount`,
                    `tsi`.`custom_total_disallowance_amount` AS `custom_total_disallowance_amount`,
                    `tsi`.`custom_total_settled_amount` AS `custom_total_settled_amount`,
                    `tsi`.`custom_total_writeoff_amount` AS `custom_total_writeoff_amount`,
                    `tsi`.`custom_total_amount_number_card` AS `custom_total_amount_number_card`,
                    `tsi`.`custom_file_upload` AS `custom_file_upload`,
                    `tsi`.`custom_transform` AS `custom_transform`,
                    `tsi`.`custom_index` AS `custom_index`,
                    `pe`.`custom_sales_invoice` AS `custom_sales_invoice`,
                    `pe`.`pe_posting_date` AS `pe_posting_date`,
                    `pe`.`pe_paid` AS `pe_paid`,
                    `pe`.`pe_tds` AS `pe_tds`,
                    `pe`.`pe_dis` AS `pe_dis`
                from
                    (`tabSales Invoice` `tsi`
                left join (
                    select
                        `tpe`.`custom_sales_invoice` AS `custom_sales_invoice`,
                        `tpe`.`posting_date` AS `pe_posting_date`,
                        sum(`tpe`.`custom_tds_amount`) AS `pe_tds`,
                        sum(`tpe`.`custom_disallowed_amount`) AS `pe_dis`,
                        sum(`tpe`.`paid_amount`) AS `pe_paid`
                    from
                        (`tabPayment Entry` `tpe`
                    join (
                        select
                            `tfy`.`year_start_date` AS `ysd`,
                            `tfy`.`year_end_date` AS `yed`
                        from
                            `tabFiscal Year` `tfy`
                        where
                            curdate() between `tfy`.`year_start_date` and `tfy`.`year_end_date`) `fy` on
                        (cast(`tpe`.`posting_date` as date) between cast(`fy`.`ysd` as date) and cast(`fy`.`yed` as date)))
                    group by
                        `tpe`.`custom_sales_invoice`) `pe` on
                    (`tsi`.`name` = `pe`.`custom_sales_invoice`))
                where
                    `tsi`.`status` <> 'Cancelled'
                group by
                    `tsi`.`name`) `pen` on
                (`pen`.`name` = `jv`.`name`))
            left join `tabYearly Due` `tyd` on
                (`pen`.`name` = `tyd`.`parent`))
            where
                `tyd`.`fiscal_year` = '2023-2024';
            """)
        
    def create_sales_invoice_report_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `veiwSales Invoice Report` AS
            SELECT
                `tsi`.`name` AS `bill_number`,
                `tsi`.`posting_date` AS `bill_date`,
                `tsi`.`entity` AS `entity`,
                `tsi`.`region` AS `region`,
                `tsi`.`branch` AS `branch`,
                `tsi`.`branch_type` AS `branch_type`,
                `tsi`.`customer` AS `customer`,
                `tsi`.`customer_group` AS `customer_group`,
                `tsi`.`custom_claim_id` AS `claim_id`,
                `tsi`.`custom_ma_claim_id` AS `ma_claim_id`,
                `tsi`.`custom_patient_name` AS `patient_name`,
                `tsi`.`custom_mrn` AS `mrn`,
                `tsi`.`status` AS `status`,
                `tsi`.`custom_insurance_name` AS `insurance_name`,
                `tsi`.`rounded_total` AS `claim_amount`,
                `tsi`.`outstanding_amount` AS `outstanding_amount`,
                coalesce(sum(`table1`.`settled_amount`) over ( partition by `tsi`.`name`), 0) AS `total_settled`,
                coalesce(sum(`table1`.`tds`) over ( partition by `tsi`.`name`), 0) AS `total_tds`,
                coalesce(sum(`table1`.`disallowance`) over ( partition by `tsi`.`name`), 0) AS `total_disallowance`,
                coalesce(sum(`table1`.`round_off`) over ( partition by `tsi`.`name`), 0) AS `total_round_off`,
                coalesce(sum(`table1`.`write_off`) over ( partition by `tsi`.`name`), 0) AS `total_write_off`,
                `table1`.`entry_type` AS `entry_type`,
                `table1`.`entry_name` AS `entry_name`,
                `table1`.`settled_amount` AS `settled_amount`,
                `table1`.`tds` AS `tds_amount`,
                `table1`.`disallowance` AS `disallowed_amount`,
                `table1`.`round_off` AS `round_off`,
                `table1`.`write_off` AS `write_off`,
                `table1`.`allocated_amount` AS `allocated_amount`,
                `table1`.`utr_number` AS `utr_number`,
                `table1`.`utr_date` AS `utr_date`,
                `table1`.`posting_date` AS `payment_posting_date`,
                `table1`.`created_date` AS `payment_created_date`,
                `tm`.`match_logic` AS `match_logic`,
                `tm`.`settlement_advice` AS `settlement_advice`,
                `tsa`.`payers_remark` AS `payers_remark`,
                `tbt`.`bank_account` AS `Bank Account`,
                `tbt`.`custom_entity` AS `Bank Entity`,
                `tbt`.`custom_region` AS `Bank Region`,
                `tbt`.`party` AS `Bank Payer`
            from
                ((((`tabSales Invoice` `tsi`
            left join (
                select
                    'Payment Entry' AS `entry_type`,
                    `tpe`.`name` AS `entry_name`,
                    `tpe`.`custom_sales_invoice` AS `bill_number`,
                    `tpe`.`posting_date` AS `posting_date`,
                    cast(`tpe`.`creation` as date) AS `created_date`,
                    ifnull(`tpe`.`paid_amount`, 0) AS `settled_amount`,
                    ifnull(`tpe`.`custom_disallowed_amount`, 0) AS `disallowance`,
                    ifnull(`tpe`.`custom_tds_amount`, 0) AS `tds`,
                    ifnull(`tpe`.`custom_round_off`, 0) AS `round_off`,
                    0 AS `write_off`,
                    `tpe`.`paid_amount` + `tpe`.`custom_tds_amount` + `tpe`.`custom_disallowed_amount` + `tpe`.`custom_round_off` AS `allocated_amount`,
                    `tpe`.`reference_no` AS `utr_number`,
                    `tpe`.`reference_date` AS `utr_date`,
                    `tpe`.`custom_matcher_id` AS `matcher_id`
                from
                    `tabPayment Entry` `tpe`
                where
                    `tpe`.`status` <> 'Cancelled'
            union all
                select
                    'Journal Entry' AS `entry_type`,
                    `tje`.`name` AS `entry_name`,
                    `tjea`.`reference_name` AS `bill_number`,
                    `tje`.`posting_date` AS `posting_date`,
                    cast(`tje`.`creation` as date) AS `created_date`,
                    0 AS `settled_amount`,
                    case
                        when `tje`.`name` like '%-DIS' then `tje`.`total_credit`
                        else 0
                    end AS `disallowance`,
                    case
                        when `tje`.`name` like '%-TDS' then `tje`.`total_credit`
                        else 0
                    end AS `tds`,
                    case
                        when `tje`.`name` like '%-RND' then `tje`.`total_credit`
                        else 0
                    end AS `round_off`,
                    case
                        when `tje`.`name` like '%-WO' then `tje`.`total_credit`
                        else 0
                    end AS `write_off`,
                    `tje`.`total_credit` AS `allocated_amount`,
                    `t`.`utr_number` AS `utr_number`,
                    `t`.`utr_date` AS `utr_date`,
                    NULL AS `matcher_id`
                from
                    ((`tabJournal Entry` `tje`
                join `tabJournal Entry Account` `tjea` on
                    (`tje`.`name` = `tjea`.`parent`))
                left join (
                    select
                        `tpe`.`custom_sales_invoice` AS `bill_number`,
                        `tpe`.`reference_no` AS `utr_number`,
                        min(`tpe`.`reference_date`) AS `utr_date`
                    from
                        `tabPayment Entry` `tpe`
                    where
                        `tpe`.`status` <> 'Cancelled'
                    group by
                        `tpe`.`custom_sales_invoice`) `t` on
                    (`t`.`bill_number` = `tjea`.`reference_name`))
                where
                    `tjea`.`account` = 'Debtors - A'
                    and `tje`.`docstatus` <> 2) `table1` on
                (`table1`.`bill_number` = `tsi`.`name`))
            left join `tabMatcher` `tm` on
                (`tm`.`name` = `table1`.`matcher_id`))
            left join `tabSettlement Advice` `tsa` on
                (`tm`.`settlement_advice` = `tsa`.`name`))
            left join `tabBank Transaction` `tbt` on
                (`table1`.`utr_number` = `tbt`.`name`));
            """)
        
    def create_journal_entry_24_25_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewJournal Entry 24-25` AS
            select
                'Journal Entry' AS `entry_type`,
                `tje`.`name` AS `entry_name`,
                `tjea`.`reference_name` AS `bill_number`,
                `tje`.`posting_date` AS `posting_date`,
                cast(`tje`.`creation` as date) AS `created_date`,
                case
                    when `tje`.`name` like '%-DIS' then `tje`.`total_credit`
                    else 0
                end AS `disallowance`,
                case
                    when `tje`.`name` like '%-TDS' then `tje`.`total_credit`
                    else 0
                end AS `tds`,
                `t`.`utr_date` AS `utr_date`
            from
                ((`tabJournal Entry` `tje`
            join `tabJournal Entry Account` `tjea` on
                (`tje`.`name` = `tjea`.`parent`))
            left join (
                select
                    `tpe`.`custom_sales_invoice` AS `bill_number`,
                    min(`tpe`.`reference_date`) AS `utr_date`
                from
                    `tabPayment Entry` `tpe`
                where
                    `tpe`.`status` <> 'Cancelled'
                group by
                    `tpe`.`custom_sales_invoice`) `t` on
                (`t`.`bill_number` = `tjea`.`reference_name`))
            where
                `tje`.`posting_date` > '2024-03-31'
                and `tjea`.`account` = 'Debtors - A'
                and `tje`.`name` not like '%-RND'
                and `tje`.`name` not like '%-WO';
            """)
        
    def create_journal_entry_summary_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewJournal Entry Summary` AS
            select
                `T`.`bill_number` AS `bill_number`,
                sum(`T`.`tds`) AS `tds`,
                sum(`T`.`disallowance`) AS `disallowance`
            from
                (
                select
                    `tjea`.`reference_name` AS `bill_number`,
                    `tje`.`custom_branch` AS `custom_branch`,
                    `tje`.`custom_entity` AS `custom_entity`,
                    `tje`.`custom_region` AS `custom_region`,
                    `tje`.`custom_branch_type` AS `custom_branch_type`,
                    case
                        when `tje`.`name` like '%-DIS' then `tje`.`total_credit`
                        else 0
                    end AS `disallowance`,
                    case
                        when `tje`.`name` like '%-TDS' then `tje`.`total_credit`
                        else 0
                    end AS `tds`
                from
                    (`tabJournal Entry` `tje`
                join `tabJournal Entry Account` `tjea`)
                where
                    `tje`.`posting_date` > '2024-03-31'
                    and `tjea`.`parent` = `tje`.`name`
                    and `tjea`.`account` = 'Debtors - A') `T`
            group by
                `T`.`bill_number`;
            """)
        
    def create_journal_entry_summary_total(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewJournal Entry Summary Total` AS
            select
                `T`.`bill_number` AS `bill_number`,
                sum(`T`.`tds`) AS `tds`,
                sum(`T`.`disallowance`) AS `disallowance`
            from
                (
                select
                    `tjea`.`reference_name` AS `bill_number`,
                    `tje`.`custom_branch` AS `custom_branch`,
                    `tje`.`custom_entity` AS `custom_entity`,
                    `tje`.`custom_region` AS `custom_region`,
                    `tje`.`custom_branch_type` AS `custom_branch_type`,
                    case
                        when `tje`.`name` like '%-DIS' then `tje`.`total_credit`
                        else 0
                    end AS `disallowance`,
                    case
                        when `tje`.`name` like '%-TDS' then `tje`.`total_credit`
                        else 0
                    end AS `tds`
                from
                    (`tabJournal Entry` `tje`
                join `tabJournal Entry Account` `tjea`)
                where
                    `tjea`.`parent` = `tje`.`name`
                    and `tjea`.`account` = 'Debtors - A') `T`
            group by
                `T`.`bill_number`;
            """)
        
    def create_journal_entry_total(slef):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewJournal Entry Total` AS
            select
                'Journal Entry' AS `entry_type`,
                `tje`.`name` AS `entry_name`,
                `tjea`.`reference_name` AS `bill_number`,
                `tje`.`posting_date` AS `posting_date`,
                cast(`tje`.`creation` as date) AS `created_date`,
                case
                    when `tje`.`name` like '%-DIS' then `tje`.`total_credit`
                    else 0
                end AS `disallowance`,
                case
                    when `tje`.`name` like '%-TDS' then `tje`.`total_credit`
                    else 0
                end AS `tds`,
                `t`.`utr_date` AS `utr_date`
            from
                ((`tabJournal Entry` `tje`
            join `tabJournal Entry Account` `tjea` on
                (`tje`.`name` = `tjea`.`parent`))
            left join (
                select
                    `tpe`.`custom_sales_invoice` AS `bill_number`,
                    min(`tpe`.`reference_date`) AS `utr_date`
                from
                    `tabPayment Entry` `tpe`
                where
                    `tpe`.`status` <> 'Cancelled'
                group by
                    `tpe`.`custom_sales_invoice`) `t` on
                (`t`.`bill_number` = `tjea`.`reference_name`))
            where
                `tjea`.`account` = 'Debtors - A'
                and `tje`.`name` not like '%-RND'
                and `tje`.`name` not like '%-WO';
            """)
           
    def create_matcher_total_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewMatcher Total` AS
            select
                `tm`.`name` AS `matcher`,
                `tm`.`sales_invoice` AS `sales_invoice`,
                `tm`.`settlement_advice` AS `settlement_advice`,
                `tm`.`match_logic` AS `match_logic`,
                `tm`.`bank_transaction` AS `bank_transaction`
            from
                (`tabMatcher` `tm`
            join `tabPayment Entry` `tpe` on
                (`tm`.`name` = `tpe`.`custom_matcher_id`))
            where
                `tpe`.`status` <> 'Cancelled';
                """)
        
    def create_payment_entry_24_25_view(self):
        frappe.db.sql(""" CREATE OR REPLACE VIEW `viewPayment Entry 24-25` AS
            select
                'Payment Entry' AS `entry_type`,
                `tpe`.`name` AS `name`,
                `tpe`.`creation` AS `creation`,
                `tpe`.`modified` AS `modified`,
                `tpe`.`modified_by` AS `modified_by`,
                `tpe`.`owner` AS `owner`,
                `tpe`.`docstatus` AS `docstatus`,
                `tpe`.`idx` AS `idx`,
                `tpe`.`naming_series` AS `naming_series`,
                `tpe`.`payment_type` AS `payment_type`,
                `tpe`.`payment_order_status` AS `payment_order_status`,
                `tpe`.`posting_date` AS `posting_date`,
                `tpe`.`company` AS `company`,
                `tpe`.`mode_of_payment` AS `mode_of_payment`,
                `tpe`.`party_type` AS `party_type`,
                `tpe`.`party` AS `party`,
                `tpe`.`party_name` AS `party_name`,
                `tpe`.`bank_account` AS `bank_account`,
                `tpe`.`party_bank_account` AS `party_bank_account`,
                `tpe`.`contact_person` AS `contact_person`,
                `tpe`.`contact_email` AS `contact_email`,
                `tpe`.`party_balance` AS `party_balance`,
                `tpe`.`paid_from` AS `paid_from`,
                `tpe`.`paid_from_account_type` AS `paid_from_account_type`,
                `tpe`.`paid_from_account_currency` AS `paid_from_account_currency`,
                `tpe`.`paid_from_account_balance` AS `paid_from_account_balance`,
                `tpe`.`paid_to` AS `paid_to`,
                `tpe`.`paid_to_account_type` AS `paid_to_account_type`,
                `tpe`.`paid_to_account_currency` AS `paid_to_account_currency`,
                `tpe`.`paid_to_account_balance` AS `paid_to_account_balance`,
                `tpe`.`paid_amount` AS `paid_amount`,
                `tpe`.`paid_amount_after_tax` AS `paid_amount_after_tax`,
                `tpe`.`source_exchange_rate` AS `source_exchange_rate`,
                `tpe`.`base_paid_amount` AS `base_paid_amount`,
                `tpe`.`base_paid_amount_after_tax` AS `base_paid_amount_after_tax`,
                `tpe`.`received_amount` AS `received_amount`,
                `tpe`.`received_amount_after_tax` AS `received_amount_after_tax`,
                `tpe`.`target_exchange_rate` AS `target_exchange_rate`,
                `tpe`.`base_received_amount` AS `base_received_amount`,
                `tpe`.`base_received_amount_after_tax` AS `base_received_amount_after_tax`,
                `tpe`.`total_allocated_amount` AS `total_allocated_amount`,
                `tpe`.`base_total_allocated_amount` AS `base_total_allocated_amount`,
                `tpe`.`unallocated_amount` AS `unallocated_amount`,
                `tpe`.`difference_amount` AS `difference_amount`,
                `tpe`.`purchase_taxes_and_charges_template` AS `purchase_taxes_and_charges_template`,
                `tpe`.`sales_taxes_and_charges_template` AS `sales_taxes_and_charges_template`,
                `tpe`.`apply_tax_withholding_amount` AS `apply_tax_withholding_amount`,
                `tpe`.`tax_withholding_category` AS `tax_withholding_category`,
                `tpe`.`base_total_taxes_and_charges` AS `base_total_taxes_and_charges`,
                `tpe`.`total_taxes_and_charges` AS `total_taxes_and_charges`,
                `tpe`.`reference_no` AS `reference_no`,
                `tpe`.`reference_date` AS `reference_date`,
                `tpe`.`clearance_date` AS `clearance_date`,
                `tpe`.`project` AS `project`,
                `tpe`.`cost_center` AS `cost_center`,
                `tpe`.`status` AS `status`,
                `tpe`.`custom_remarks` AS `custom_remarks`,
                `tpe`.`remarks` AS `remarks`,
                `tpe`.`letter_head` AS `letter_head`,
                `tpe`.`print_heading` AS `print_heading`,
                `tpe`.`bank` AS `bank`,
                `tpe`.`bank_account_no` AS `bank_account_no`,
                `tpe`.`payment_order` AS `payment_order`,
                `tpe`.`auto_repeat` AS `auto_repeat`,
                `tpe`.`amended_from` AS `amended_from`,
                `tpe`.`title` AS `title`,
                `tpe`.`_user_tags` AS `_user_tags`,
                `tpe`.`_comments` AS `_comments`,
                `tpe`.`_assign` AS `_assign`,
                `tpe`.`_liked_by` AS `_liked_by`,
                `tpe`.`region` AS `region`,
                `tpe`.`branch` AS `branch`,
                `tpe`.`branch_type` AS `branch_type`,
                `tpe`.`entity` AS `entity`,
                `tpe`.`custom_sales_invoice` AS `custom_sales_invoice`,
                `tpe`.`custom_tds_amount` AS `custom_tds_amount`,
                `tpe`.`custom_disallowed_amount` AS `custom_disallowed_amount`,
                `tpe`.`custom_due_date` AS `custom_due_date`,
                `tpe`.`custom_posting_year` AS `custom_posting_year`,
                `tpe`.`custom_posting_month` AS `custom_posting_month`,
                `tpe`.`custom_utr_year` AS `custom_utr_year`,
                `tpe`.`custom_utr_month` AS `custom_utr_month`,
                `tpe`.`custom_file_upload` AS `custom_file_upload`,
                `tpe`.`custom_transform` AS `custom_transform`,
                `tpe`.`custom_parent_doc` AS `custom_parent_doc`,
                `tpe`.`custom_index` AS `custom_index`
            from
                `tabPayment Entry` `tpe`
            where
                `tpe`.`status` <> 'Cancelled'
                and `tpe`.`posting_date` > '2024-03-31';
            """)
        
    def create_payment_entry_summary_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewPayment Entry Summary` AS
            select
                `tpe`.`custom_sales_invoice` AS `bill_number`,
                sum(`tpe`.`paid_amount`) AS `settled`,
                sum(`tpe`.`custom_tds_amount`) AS `tds`,
                sum(`tpe`.`custom_disallowed_amount`) AS `disallowance`
            from
                `tabPayment Entry` `tpe`
            where
                `tpe`.`posting_date` > '2024-03-31'
                and `tpe`.`status` <> 'Cancelled'
            group by
                `tpe`.`custom_sales_invoice`;
            """)
        
    def create_payment_entry_summary_total_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewPayment Entry Summary Total` AS
        select
            `tpe`.`custom_sales_invoice` AS `bill_number`,
            sum(`tpe`.`paid_amount`) AS `settled`,
            sum(`tpe`.`custom_tds_amount`) AS `tds`,
            sum(`tpe`.`custom_disallowed_amount`) AS `disallowance`
        from
            `tabPayment Entry` `tpe`
        where
            `tpe`.`status` <> 'Cancelled'
        group by
            `tpe`.`custom_sales_invoice`;
        """)
    
    def create_payment_entry_total_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewPayment Entry Total` AS
            select
                'Payment Entry' AS `entry_type`,
                `tpe`.`name` AS `name`,
                `tpe`.`creation` AS `creation`,
                `tpe`.`modified` AS `modified`,
                `tpe`.`modified_by` AS `modified_by`,
                `tpe`.`owner` AS `owner`,
                `tpe`.`docstatus` AS `docstatus`,
                `tpe`.`idx` AS `idx`,
                `tpe`.`naming_series` AS `naming_series`,
                `tpe`.`payment_type` AS `payment_type`,
                `tpe`.`payment_order_status` AS `payment_order_status`,
                `tpe`.`posting_date` AS `posting_date`,
                `tpe`.`company` AS `company`,
                `tpe`.`mode_of_payment` AS `mode_of_payment`,
                `tpe`.`party_type` AS `party_type`,
                `tpe`.`party` AS `party`,
                `tpe`.`party_name` AS `party_name`,
                `tpe`.`bank_account` AS `bank_account`,
                `tpe`.`party_bank_account` AS `party_bank_account`,
                `tpe`.`contact_person` AS `contact_person`,
                `tpe`.`contact_email` AS `contact_email`,
                `tpe`.`party_balance` AS `party_balance`,
                `tpe`.`paid_from` AS `paid_from`,
                `tpe`.`paid_from_account_type` AS `paid_from_account_type`,
                `tpe`.`paid_from_account_currency` AS `paid_from_account_currency`,
                `tpe`.`paid_from_account_balance` AS `paid_from_account_balance`,
                `tpe`.`paid_to` AS `paid_to`,
                `tpe`.`paid_to_account_type` AS `paid_to_account_type`,
                `tpe`.`paid_to_account_currency` AS `paid_to_account_currency`,
                `tpe`.`paid_to_account_balance` AS `paid_to_account_balance`,
                `tpe`.`paid_amount` AS `paid_amount`,
                `tpe`.`paid_amount_after_tax` AS `paid_amount_after_tax`,
                `tpe`.`source_exchange_rate` AS `source_exchange_rate`,
                `tpe`.`base_paid_amount` AS `base_paid_amount`,
                `tpe`.`base_paid_amount_after_tax` AS `base_paid_amount_after_tax`,
                `tpe`.`received_amount` AS `received_amount`,
                `tpe`.`received_amount_after_tax` AS `received_amount_after_tax`,
                `tpe`.`target_exchange_rate` AS `target_exchange_rate`,
                `tpe`.`base_received_amount` AS `base_received_amount`,
                `tpe`.`base_received_amount_after_tax` AS `base_received_amount_after_tax`,
                `tpe`.`total_allocated_amount` AS `total_allocated_amount`,
                `tpe`.`base_total_allocated_amount` AS `base_total_allocated_amount`,
                `tpe`.`unallocated_amount` AS `unallocated_amount`,
                `tpe`.`difference_amount` AS `difference_amount`,
                `tpe`.`purchase_taxes_and_charges_template` AS `purchase_taxes_and_charges_template`,
                `tpe`.`sales_taxes_and_charges_template` AS `sales_taxes_and_charges_template`,
                `tpe`.`apply_tax_withholding_amount` AS `apply_tax_withholding_amount`,
                `tpe`.`tax_withholding_category` AS `tax_withholding_category`,
                `tpe`.`base_total_taxes_and_charges` AS `base_total_taxes_and_charges`,
                `tpe`.`total_taxes_and_charges` AS `total_taxes_and_charges`,
                `tpe`.`reference_no` AS `reference_no`,
                `tpe`.`reference_date` AS `reference_date`,
                `tpe`.`clearance_date` AS `clearance_date`,
                `tpe`.`project` AS `project`,
                `tpe`.`cost_center` AS `cost_center`,
                `tpe`.`status` AS `status`,
                `tpe`.`custom_remarks` AS `custom_remarks`,
                `tpe`.`remarks` AS `remarks`,
                `tpe`.`letter_head` AS `letter_head`,
                `tpe`.`print_heading` AS `print_heading`,
                `tpe`.`bank` AS `bank`,
                `tpe`.`bank_account_no` AS `bank_account_no`,
                `tpe`.`payment_order` AS `payment_order`,
                `tpe`.`auto_repeat` AS `auto_repeat`,
                `tpe`.`amended_from` AS `amended_from`,
                `tpe`.`title` AS `title`,
                `tpe`.`_user_tags` AS `_user_tags`,
                `tpe`.`_comments` AS `_comments`,
                `tpe`.`_assign` AS `_assign`,
                `tpe`.`_liked_by` AS `_liked_by`,
                `tpe`.`region` AS `region`,
                `tpe`.`branch` AS `branch`,
                `tpe`.`branch_type` AS `branch_type`,
                `tpe`.`entity` AS `entity`,
                `tpe`.`custom_sales_invoice` AS `custom_sales_invoice`,
                `tpe`.`custom_tds_amount` AS `custom_tds_amount`,
                `tpe`.`custom_disallowed_amount` AS `custom_disallowed_amount`,
                `tpe`.`custom_due_date` AS `custom_due_date`,
                `tpe`.`custom_posting_year` AS `custom_posting_year`,
                `tpe`.`custom_posting_month` AS `custom_posting_month`,
                `tpe`.`custom_utr_year` AS `custom_utr_year`,
                `tpe`.`custom_utr_month` AS `custom_utr_month`,
                `tpe`.`custom_file_upload` AS `custom_file_upload`,
                `tpe`.`custom_transform` AS `custom_transform`,
                `tpe`.`custom_parent_doc` AS `custom_parent_doc`,
                `tpe`.`custom_index` AS `custom_index`,
                `tpe`.`custom_matcher_id` AS `custom_matcher_id`
            from
                `tabPayment Entry` `tpe`
            where
                `tpe`.`status` <> 'Cancelled';
            """)
        
    def create_sales_invoice_balance_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Balance` AS
            select
                `tsi`.`name` AS `name`,
                `tsi`.`custom_total_tds_amount` AS `Total_TDS`,
                `tsi`.`custom_total_disallowance_amount` AS `Total_Disallowance`,
                `tsi`.`custom_total_writeoff_amount` AS `Total_Write_Off`,
                `tsi`.`custom_total_settled_amount` AS `Settled_Amount`,
                `tsi`.`custom_total_tds_amount` + `tsi`.`custom_total_disallowance_amount` + `tsi`.`custom_total_writeoff_amount` + `tsi`.`custom_total_settled_amount` AS `Total_Paid_Amount`,
                `tsi`.`outstanding_amount` AS `Outstanding`,
                `tsi`.`total` AS `Claim_Amount`,
                abs(`tsi`.`custom_total_tds_amount` + `tsi`.`custom_total_disallowance_amount` + `tsi`.`custom_total_writeoff_amount` + `tsi`.`custom_total_settled_amount` - `tsi`.`total`) AS `Difference_Amount`
            from
                ((`tabSales Invoice` `tsi`
            join `tabPayment Entry` `tpe` on
                (`tsi`.`name` = `tpe`.`custom_sales_invoice`))
            join (
                select
                    `tabJournal Entry Account`.`name` AS `name`,
                    `tabJournal Entry Account`.`creation` AS `creation`,
                    `tabJournal Entry Account`.`modified` AS `modified`,
                    `tabJournal Entry Account`.`modified_by` AS `modified_by`,
                    `tabJournal Entry Account`.`owner` AS `owner`,
                    `tabJournal Entry Account`.`docstatus` AS `docstatus`,
                    `tabJournal Entry Account`.`idx` AS `idx`,
                    `tabJournal Entry Account`.`account` AS `account`,
                    `tabJournal Entry Account`.`account_type` AS `account_type`,
                    `tabJournal Entry Account`.`balance` AS `balance`,
                    `tabJournal Entry Account`.`bank_account` AS `bank_account`,
                    `tabJournal Entry Account`.`party_type` AS `party_type`,
                    `tabJournal Entry Account`.`party` AS `party`,
                    `tabJournal Entry Account`.`party_balance` AS `party_balance`,
                    `tabJournal Entry Account`.`cost_center` AS `cost_center`,
                    `tabJournal Entry Account`.`project` AS `project`,
                    `tabJournal Entry Account`.`account_currency` AS `account_currency`,
                    `tabJournal Entry Account`.`exchange_rate` AS `exchange_rate`,
                    `tabJournal Entry Account`.`debit_in_account_currency` AS `debit_in_account_currency`,
                    `tabJournal Entry Account`.`debit` AS `debit`,
                    `tabJournal Entry Account`.`credit_in_account_currency` AS `credit_in_account_currency`,
                    `tabJournal Entry Account`.`credit` AS `credit`,
                    `tabJournal Entry Account`.`reference_type` AS `reference_type`,
                    `tabJournal Entry Account`.`reference_name` AS `reference_name`,
                    `tabJournal Entry Account`.`reference_due_date` AS `reference_due_date`,
                    `tabJournal Entry Account`.`reference_detail_no` AS `reference_detail_no`,
                    `tabJournal Entry Account`.`is_advance` AS `is_advance`,
                    `tabJournal Entry Account`.`user_remark` AS `user_remark`,
                    `tabJournal Entry Account`.`against_account` AS `against_account`,
                    `tabJournal Entry Account`.`parent` AS `parent`,
                    `tabJournal Entry Account`.`parentfield` AS `parentfield`,
                    `tabJournal Entry Account`.`parenttype` AS `parenttype`,
                    `tabJournal Entry Account`.`region` AS `region`,
                    `tabJournal Entry Account`.`branch` AS `branch`,
                    `tabJournal Entry Account`.`branch_type` AS `branch_type`,
                    `tabJournal Entry Account`.`entity` AS `entity`
                from
                    `tabJournal Entry Account`
                group by
                    `tabJournal Entry Account`.`reference_name`) `tjea` on
                (`tsi`.`name` <> `tjea`.`reference_name`));
                """)
        
    def create_sales_invoice_current_year_view(self):
        # Updated viewSales Invoice Current Year - added total_claim_amount to get total_claim_amount in viewSales Invoice Current Year Breakup
        frappe.db.sql("""
            CREATE OR REPLACE VIEW `viewSales Invoice Current Year` AS
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
        
    def create_sales_invoice_current_year_breakup_view(self):
         # Updated Added Claim_amount in viewSales Invoice Current Year Breakup to get total_claim_amount in viewcurrent_year_si_checklist
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Current Year Breakup` AS
            select
                `vsicy`.`bill_number` AS `bill_number`,
                `vsicy`.`posting_date` AS `bill_date`,
                `vsicy`.`claim_amount` AS `current_claim_amount`,
                `vsicy`.`total_claim_amount` AS `claim_amount`,
                coalesce(`vss`.`settled`, 0) AS `settled_amount`,
                coalesce(`vss`.`tds`, 0) AS `tds_amount`,
                coalesce(`vss`.`disallowance`, 0) AS `disallowed_amount`,
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
        
    def create_sales_invoice_payers_remark_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Payers Remark` AS
            select
                `tsi`.`name` AS `name`,
                `tm`.`match_logic` AS `match_logic`,
                `tm`.`settlement_advice` AS `settlement_advice`,
                `tsa`.`payers_remark` AS `payers_remark`,
                row_number() over ( partition by `tsi`.`name`
            order by
                `tsi`.`name`) AS `row_count`
            from
                ((`tabSales Invoice` `tsi`
            join `tabMatcher` `tm` on
                (`tsi`.`name` = `tm`.`sales_invoice`))
            left join `tabSettlement Advice` `tsa` on
                (`tm`.`settlement_advice` = `tsa`.`name`))
            where
                `tsi`.`status` not in ('Cancelled', 'Unpaid')
                and `tm`.`status` = 'Processed';
            """)
        
    def create_sales_invoice_reference_24_25_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Reference 24-25` AS
            select
                `vje`.`entry_type` AS `entry_type`,
                `vje`.`entry_name` AS `entry_name`,
                `vje`.`bill_number` AS `bill_number`,
                0 AS `settled`,
                `vje`.`tds` AS `tds`,
                `vje`.`disallowance` AS `disallowance`,
                `vje`.`tds` + `vje`.`disallowance` AS `allocated_amount`,
                `vje`.`posting_date` AS `posting_date`,
                `vje`.`created_date` AS `created_date`,
                `vje`.`utr_date` AS `utr_date`,
                NULL AS `utr_number`
            from
                `viewJournal Entry 24-25` `vje`
            union
            select
                `vpe`.`entry_type` AS `entry_type`,
                `vpe`.`name` AS `entry_name`,
                `vpe`.`custom_sales_invoice` AS `bill_number`,
                `vpe`.`paid_amount` AS `settled`,
                `vpe`.`custom_tds_amount` AS `tds`,
                `vpe`.`custom_disallowed_amount` AS `disallowance`,
                `vpe`.`total_allocated_amount` AS `allocated_amount`,
                `vpe`.`posting_date` AS `posting_date`,
                cast(`vpe`.`creation` as date) AS `created_date`,
                `vpe`.`reference_date` AS `utr_date`,
                `vpe`.`reference_no` AS `utr_number`
            from
                `viewPayment Entry 24-25` `vpe`;
            """)
        
    def create_sales_invoice_reference_total_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Reference Total` AS
            select
                `vje`.`entry_type` AS `entry_type`,
                `vje`.`entry_name` AS `entry_name`,
                `vje`.`bill_number` AS `bill_number`,
                0 AS `settled`,
                `vje`.`tds` AS `tds`,
                `vje`.`disallowance` AS `disallowance`,
                `vje`.`tds` + `vje`.`disallowance` AS `allocated_amount`,
                `vje`.`posting_date` AS `posting_date`,
                `vje`.`created_date` AS `created_date`,
                `vje`.`utr_date` AS `utr_date`,
                NULL AS `utr_number`,
                NULL AS `matcher_id`
            from
                `viewJournal Entry Total` `vje`
            union
            select
                `vpe`.`entry_type` AS `entry_type`,
                `vpe`.`name` AS `entry_name`,
                `vpe`.`custom_sales_invoice` AS `bill_number`,
                `vpe`.`paid_amount` AS `settled`,
                `vpe`.`custom_tds_amount` AS `tds`,
                `vpe`.`custom_disallowed_amount` AS `disallowance`,
                `vpe`.`total_allocated_amount` AS `allocated_amount`,
                `vpe`.`posting_date` AS `posting_date`,
                cast(`vpe`.`creation` as date) AS `created_date`,
                `vpe`.`reference_date` AS `utr_date`,
                `vpe`.`reference_no` AS `utr_number`,
                `vpe`.`custom_matcher_id` AS `matcher_id`
            from
                `viewPayment Entry Total` `vpe`;
            """)
        
    def create_sales_invoice_report_24_25_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Report 24-25` AS
            select
                `vsicyb`.`bill_number` AS `Bill Number`,
                `vsicyb`.`bill_date` AS `Bill Date`,
                `vsicyb`.`entity` AS `Entity`,
                `vsicyb`.`region` AS `Region`,
                `vsicyb`.`branch` AS `Branch`,
                `vsicyb`.`branch_type` AS `Branch Type`,
                `vsicyb`.`customer` AS `Customer`,
                `vsicyb`.`customer_group` AS `Customer Group`,
                `vsicyb`.`claim_id` AS `Claim ID`,
                `vsicyb`.`ma_claim_id` AS `MA Claim ID`,
                `vsicyb`.`patient_name` AS `Patient Name`,
                `vsicyb`.`mrn` AS `MRN`,
                `vsicyb`.`status` AS `Status`,
                `vsicyb`.`insurance_name` AS `Insurance Name`,
                `vsicyb`.`current_claim_amount` AS `Claim Amount`,
                `vsicyb`.`settled_amount` AS `Total Settled Amount`,
                `vsicyb`.`tds_amount` AS `Total TDS Amount`,
                `vsicyb`.`disallowed_amount` AS `Total Disallowance Amount`,
                `vsicyb`.`outstanding_amount` AS `Outstanding Amount`,
                `vsir`.`entry_type` AS `Entry Type`,
                `vsir`.`entry_name` AS `Entry Name`,
                `vsir`.`settled` AS `Settled Amount`,
                `vsir`.`tds` AS `TDS Amount`,
                `vsir`.`disallowance` AS `Disallowed Amount`,
                `vsir`.`allocated_amount` AS `Allocated Amount`,
                `vsir`.`utr_date` AS `UTR Date`,
                `vsir`.`utr_number` AS `UTR Number`,
                `vsir`.`posting_date` AS `Payment Posting Date`,
                `vsir`.`created_date` AS `Payment Created Date`,
                `vm`.`match_logic` AS `Match Logic`,
                `vm`.`settlement_advice` AS `Settlement Advice`
            from
                ((`viewSales Invoice Current Year Breakup` `vsicyb`
            left join `viewSales Invoice Reference 24-25` `vsir` on
                (`vsicyb`.`bill_number` = `vsir`.`bill_number`))
            left join `viewMatcher` `vm` on
                (`vsicyb`.`bill_number` = `vm`.`sales_invoice`
                    and `vsir`.`utr_number` = `vm`.`bank_transaction`))
            order by
                `vsicyb`.`bill_number`,
                `vsir`.`posting_date`;
            """)
        
    def create_sales_invoice_report_24_25_with_row_number_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Report 24-25 with Row Number` AS
            select
                `vsir`.`Bill Number` AS `Bill Number`,
                `vsir`.`Bill Date` AS `Bill Date`,
                `vsir`.`Entity` AS `Entity`,
                `vsir`.`Region` AS `Region`,
                `vsir`.`Branch` AS `Branch`,
                `vsir`.`Branch Type` AS `Branch Type`,
                `vsir`.`Customer` AS `Customer`,
                `vsir`.`Customer Group` AS `Customer Group`,
                `vsir`.`Claim ID` AS `Claim ID`,
                `vsir`.`MA Claim ID` AS `MA Claim ID`,
                `vsir`.`Patient Name` AS `Patient Name`,
                `vsir`.`MRN` AS `MRN`,
                `vsir`.`Status` AS `Status`,
                `vsir`.`Insurance Name` AS `Insurance Name`,
                `vsir`.`Claim Amount` AS `Claim Amount`,
                `vsir`.`Total Settled Amount` AS `Total Settled Amount`,
                `vsir`.`Total TDS Amount` AS `Total TDS Amount`,
                `vsir`.`Total Disallowance Amount` AS `Total Disallowance Amount`,
                `vsir`.`Outstanding Amount` AS `Outstanding Amount`,
                `vsir`.`Entry Type` AS `Entry Type`,
                `vsir`.`Entry Name` AS `Entry Name`,
                `vsir`.`Settled Amount` AS `Settled Amount`,
                `vsir`.`TDS Amount` AS `TDS Amount`,
                `vsir`.`Disallowed Amount` AS `Disallowed Amount`,
                `vsir`.`Allocated Amount` AS `Allocated Amount`,
                `vsir`.`UTR Date` AS `UTR Date`,
                `vsir`.`UTR Number` AS `UTR Number`,
                `vsir`.`Payment Posting Date` AS `Payment Posting Date`,
                `vsir`.`Payment Created Date` AS `Payment Created Date`,
                `vsir`.`Match Logic` AS `Match Logic`,
                `vsir`.`Settlement Advice` AS `Settlement Advice`,
                row_number() over ( partition by `vsir`.`Bill Number`
            order by
                `vsir`.`Bill Number`) AS `row_count`
            from
                `viewSales Invoice Report 24-25` `vsir`;
            """)
        
    def create_sales_invoice_report_total_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Report Total` AS
            select
                `vsicyb`.`bill_number` AS `Bill Number`,
                `vsicyb`.`bill_date` AS `Bill Date`,
                `vsicyb`.`entity` AS `Entity`,
                `vsicyb`.`region` AS `Region`,
                `vsicyb`.`branch` AS `Branch`,
                `vsicyb`.`branch_type` AS `Branch Type`,
                `vsicyb`.`customer` AS `Customer`,
                `vsicyb`.`customer_group` AS `Customer Group`,
                `vsicyb`.`claim_id` AS `Claim ID`,
                `vsicyb`.`ma_claim_id` AS `MA Claim ID`,
                `vsicyb`.`patient_name` AS `Patient Name`,
                `vsicyb`.`mrn` AS `MRN`,
                `vsicyb`.`status` AS `Status`,
                `vsicyb`.`insurance_name` AS `Insurance Name`,
                `vsicyb`.`current_claim_amount` AS `Claim Amount`,
                `vsicyb`.`settled_amount` AS `Total Settled Amount`,
                `vsicyb`.`tds_amount` AS `Total TDS Amount`,
                `vsicyb`.`disallowed_amount` AS `Total Disallowance Amount`,
                `vsicyb`.`outstanding_amount` AS `Outstanding Amount`,
                `vsir`.`entry_type` AS `Entry Type`,
                `vsir`.`entry_name` AS `Entry Name`,
                `vsir`.`settled` AS `Settled Amount`,
                `vsir`.`tds` AS `TDS Amount`,
                `vsir`.`disallowance` AS `Disallowed Amount`,
                `vsir`.`allocated_amount` AS `Allocated Amount`,
                `vsir`.`utr_date` AS `UTR Date`,
                `vsir`.`utr_number` AS `UTR Number`,
                `vsir`.`posting_date` AS `Payment Posting Date`,
                `vsir`.`created_date` AS `Payment Created Date`,
                `vm`.`match_logic` AS `Match Logic`,
                `vm`.`settlement_advice` AS `Settlement Advice`
            from
                ((`viewSales Invoice Total Breakup` `vsicyb`
            left join `viewSales Invoice Reference Total` `vsir` on
                (`vsicyb`.`bill_number` = `vsir`.`bill_number`))
            left join `viewMatcher Total` `vm` on
                (`vm`.`matcher` = `vsir`.`matcher_id`))
            order by
                `vsicyb`.`bill_number`,
                `vsir`.`posting_date`;
            """)
        
    def create_sales_invoice_report_total_with_row_number_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Report Total with Row Number` AS
            select
                `vsir`.`Bill Number` AS `Bill Number`,
                `vsir`.`Bill Date` AS `Bill Date`,
                `vsir`.`Entity` AS `Entity`,
                `vsir`.`Region` AS `Region`,
                `vsir`.`Branch` AS `Branch`,
                `vsir`.`Branch Type` AS `Branch Type`,
                `vsir`.`Customer` AS `Customer`,
                `vsir`.`Customer Group` AS `Customer Group`,
                `vsir`.`Claim ID` AS `Claim ID`,
                `vsir`.`MA Claim ID` AS `MA Claim ID`,
                `vsir`.`Patient Name` AS `Patient Name`,
                `vsir`.`MRN` AS `MRN`,
                `vsir`.`Status` AS `Status`,
                `vsir`.`Insurance Name` AS `Insurance Name`,
                `vsir`.`Claim Amount` AS `Claim Amount`,
                `vsir`.`Total Settled Amount` AS `Total Settled Amount`,
                `vsir`.`Total TDS Amount` AS `Total TDS Amount`,
                `vsir`.`Total Disallowance Amount` AS `Total Disallowance Amount`,
                `vsir`.`Outstanding Amount` AS `Outstanding Amount`,
                `vsir`.`Entry Type` AS `Entry Type`,
                `vsir`.`Entry Name` AS `Entry Name`,
                `vsir`.`Settled Amount` AS `Settled Amount`,
                `vsir`.`TDS Amount` AS `TDS Amount`,
                `vsir`.`Disallowed Amount` AS `Disallowed Amount`,
                `vsir`.`Allocated Amount` AS `Allocated Amount`,
                `vsir`.`UTR Date` AS `UTR Date`,
                `vsir`.`UTR Number` AS `UTR Number`,
                `vsir`.`Payment Posting Date` AS `Payment Posting Date`,
                `vsir`.`Payment Created Date` AS `Payment Created Date`,
                `vsir`.`Match Logic` AS `Match Logic`,
                `vsir`.`Settlement Advice` AS `Settlement Advice`,
                row_number() over ( partition by `vsir`.`Bill Number`
            order by
                `vsir`.`Bill Number`) AS `row_count`
            from
                `viewSales Invoice Report Total` `vsir`;
            """)
        
    def create_sales_invoice_summary_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice Summary` AS
            select
                `tyd`.`due_amount` AS `due_amount`,
                `tsi`.`name` AS `name`,
                `tsi`.`creation` AS `creation`,
                `tsi`.`modified` AS `modified`,
                `tsi`.`modified_by` AS `modified_by`,
                `tsi`.`owner` AS `owner`,
                `tsi`.`docstatus` AS `docstatus`,
                `tsi`.`idx` AS `idx`,
                `tsi`.`title` AS `title`,
                `tsi`.`bill_no` AS `bill_no`,
                `tsi`.`naming_series` AS `naming_series`,
                `tsi`.`customer` AS `customer`,
                `tsi`.`customer_name` AS `customer_name`,
                `tsi`.`tax_id` AS `tax_id`,
                `tsi`.`company` AS `company`,
                `tsi`.`company_tax_id` AS `company_tax_id`,
                `tsi`.`posting_date` AS `posting_date`,
                `tsi`.`posting_time` AS `posting_time`,
                `tsi`.`set_posting_time` AS `set_posting_time`,
                `tsi`.`due_date` AS `due_date`,
                `tsi`.`is_pos` AS `is_pos`,
                `tsi`.`pos_profile` AS `pos_profile`,
                `tsi`.`is_consolidated` AS `is_consolidated`,
                `tsi`.`is_return` AS `is_return`,
                `tsi`.`return_against` AS `return_against`,
                `tsi`.`update_billed_amount_in_sales_order` AS `update_billed_amount_in_sales_order`,
                `tsi`.`is_debit_note` AS `is_debit_note`,
                `tsi`.`amended_from` AS `amended_from`,
                `tsi`.`cost_center` AS `cost_center`,
                `tsi`.`project` AS `project`,
                `tsi`.`currency` AS `currency`,
                `tsi`.`conversion_rate` AS `conversion_rate`,
                `tsi`.`selling_price_list` AS `selling_price_list`,
                `tsi`.`price_list_currency` AS `price_list_currency`,
                `tsi`.`plc_conversion_rate` AS `plc_conversion_rate`,
                `tsi`.`ignore_pricing_rule` AS `ignore_pricing_rule`,
                `tsi`.`scan_barcode` AS `scan_barcode`,
                `tsi`.`update_stock` AS `update_stock`,
                `tsi`.`set_warehouse` AS `set_warehouse`,
                `tsi`.`set_target_warehouse` AS `set_target_warehouse`,
                `tsi`.`total_qty` AS `total_qty`,
                `tsi`.`total_net_weight` AS `total_net_weight`,
                `tsi`.`base_total` AS `base_total`,
                `tsi`.`base_net_total` AS `base_net_total`,
                `tsi`.`total` AS `total`,
                `tsi`.`net_total` AS `net_total`,
                `tsi`.`tax_category` AS `tax_category`,
                `tsi`.`taxes_and_charges` AS `taxes_and_charges`,
                `tsi`.`shipping_rule` AS `shipping_rule`,
                `tsi`.`incoterm` AS `incoterm`,
                `tsi`.`named_place` AS `named_place`,
                `tsi`.`base_total_taxes_and_charges` AS `base_total_taxes_and_charges`,
                `tsi`.`total_taxes_and_charges` AS `total_taxes_and_charges`,
                `tsi`.`base_grand_total` AS `base_grand_total`,
                `tsi`.`base_rounding_adjustment` AS `base_rounding_adjustment`,
                `tsi`.`base_rounded_total` AS `base_rounded_total`,
                `tsi`.`base_in_words` AS `base_in_words`,
                `tsi`.`grand_total` AS `grand_total`,
                `tsi`.`rounding_adjustment` AS `rounding_adjustment`,
                `tsi`.`use_company_roundoff_cost_center` AS `use_company_roundoff_cost_center`,
                `tsi`.`rounded_total` AS `rounded_total`,
                `tsi`.`in_words` AS `in_words`,
                `tsi`.`total_advance` AS `total_advance`,
                `tsi`.`outstanding_amount` AS `outstanding_amount`,
                `tsi`.`disable_rounded_total` AS `disable_rounded_total`,
                `tsi`.`apply_discount_on` AS `apply_discount_on`,
                `tsi`.`base_discount_amount` AS `base_discount_amount`,
                `tsi`.`is_cash_or_non_trade_discount` AS `is_cash_or_non_trade_discount`,
                `tsi`.`additional_discount_account` AS `additional_discount_account`,
                `tsi`.`additional_discount_percentage` AS `additional_discount_percentage`,
                `tsi`.`discount_amount` AS `discount_amount`,
                `tsi`.`other_charges_calculation` AS `other_charges_calculation`,
                `tsi`.`total_billing_hours` AS `total_billing_hours`,
                `tsi`.`total_billing_amount` AS `total_billing_amount`,
                `tsi`.`cash_bank_account` AS `cash_bank_account`,
                `tsi`.`base_paid_amount` AS `base_paid_amount`,
                `tsi`.`paid_amount` AS `paid_amount`,
                `tsi`.`base_change_amount` AS `base_change_amount`,
                `tsi`.`change_amount` AS `change_amount`,
                `tsi`.`account_for_change_amount` AS `account_for_change_amount`,
                `tsi`.`allocate_advances_automatically` AS `allocate_advances_automatically`,
                `tsi`.`only_include_allocated_payments` AS `only_include_allocated_payments`,
                `tsi`.`write_off_amount` AS `write_off_amount`,
                `tsi`.`base_write_off_amount` AS `base_write_off_amount`,
                `tsi`.`write_off_outstanding_amount_automatically` AS `write_off_outstanding_amount_automatically`,
                `tsi`.`write_off_account` AS `write_off_account`,
                `tsi`.`write_off_cost_center` AS `write_off_cost_center`,
                `tsi`.`redeem_loyalty_points` AS `redeem_loyalty_points`,
                `tsi`.`loyalty_points` AS `loyalty_points`,
                `tsi`.`loyalty_amount` AS `loyalty_amount`,
                `tsi`.`loyalty_program` AS `loyalty_program`,
                `tsi`.`loyalty_redemption_account` AS `loyalty_redemption_account`,
                `tsi`.`loyalty_redemption_cost_center` AS `loyalty_redemption_cost_center`,
                `tsi`.`customer_address` AS `customer_address`,
                `tsi`.`address_display` AS `address_display`,
                `tsi`.`contact_person` AS `contact_person`,
                `tsi`.`contact_display` AS `contact_display`,
                `tsi`.`contact_mobile` AS `contact_mobile`,
                `tsi`.`contact_email` AS `contact_email`,
                `tsi`.`territory` AS `territory`,
                `tsi`.`shipping_address_name` AS `shipping_address_name`,
                `tsi`.`shipping_address` AS `shipping_address`,
                `tsi`.`dispatch_address_name` AS `dispatch_address_name`,
                `tsi`.`dispatch_address` AS `dispatch_address`,
                `tsi`.`company_address` AS `company_address`,
                `tsi`.`company_address_display` AS `company_address_display`,
                `tsi`.`ignore_default_payment_terms_template` AS `ignore_default_payment_terms_template`,
                `tsi`.`payment_terms_template` AS `payment_terms_template`,
                `tsi`.`tc_name` AS `tc_name`,
                `tsi`.`terms` AS `terms`,
                `tsi`.`po_no` AS `po_no`,
                `tsi`.`po_date` AS `po_date`,
                `tsi`.`debit_to` AS `debit_to`,
                `tsi`.`party_account_currency` AS `party_account_currency`,
                `tsi`.`is_opening` AS `is_opening`,
                `tsi`.`unrealized_profit_loss_account` AS `unrealized_profit_loss_account`,
                `tsi`.`against_income_account` AS `against_income_account`,
                `tsi`.`sales_partner` AS `sales_partner`,
                `tsi`.`amount_eligible_for_commission` AS `amount_eligible_for_commission`,
                `tsi`.`commission_rate` AS `commission_rate`,
                `tsi`.`total_commission` AS `total_commission`,
                `tsi`.`letter_head` AS `letter_head`,
                `tsi`.`group_same_items` AS `group_same_items`,
                `tsi`.`select_print_heading` AS `select_print_heading`,
                `tsi`.`language` AS `language`,
                `tsi`.`from_date` AS `from_date`,
                `tsi`.`auto_repeat` AS `auto_repeat`,
                `tsi`.`to_date` AS `to_date`,
                `tsi`.`status` AS `status`,
                `tsi`.`inter_company_invoice_reference` AS `inter_company_invoice_reference`,
                `tsi`.`campaign` AS `campaign`,
                `tsi`.`represents_company` AS `represents_company`,
                `tsi`.`source` AS `source`,
                `tsi`.`customer_group` AS `customer_group`,
                `tsi`.`is_internal_customer` AS `is_internal_customer`,
                `tsi`.`is_discounted` AS `is_discounted`,
                `tsi`.`remarks` AS `remarks`,
                `tsi`.`repost_required` AS `repost_required`,
                `tsi`.`_user_tags` AS `_user_tags`,
                `tsi`.`_comments` AS `_comments`,
                `tsi`.`_assign` AS `_assign`,
                `tsi`.`_liked_by` AS `_liked_by`,
                `tsi`.`_seen` AS `_seen`,
                `tsi`.`custom_bill_no` AS `custom_bill_no`,
                `tsi`.`region` AS `region`,
                `tsi`.`branch` AS `branch`,
                `tsi`.`branch_type` AS `branch_type`,
                `tsi`.`entity` AS `entity`,
                `tsi`.`custom_insurance_name` AS `custom_insurance_name`,
                `tsi`.`update_billed_amount_in_delivery_note` AS `update_billed_amount_in_delivery_note`,
                `tsi`.`dont_create_loyalty_points` AS `dont_create_loyalty_points`,
                `tsi`.`custom_mrn` AS `custom_mrn`,
                `tsi`.`custom_claim_id` AS `custom_claim_id`,
                `tsi`.`total_outstanding_amount` AS `total_outstanding_amount`,
                `tsi`.`custom_ma_claim_id` AS `custom_ma_claim_id`,
                `tsi`.`custom_patient_name` AS `custom_patient_name`,
                `tsi`.`custom_payer_name` AS `custom_payer_name`,
                `tsi`.`sales_status1` AS `sales_status1`,
                `tsi`.`custom_year` AS `custom_year`,
                `tsi`.`custom_month` AS `custom_month`,
                `tsi`.`update_outstanding_for_self` AS `update_outstanding_for_self`,
                `tsi`.`custom_tds_amount` AS `custom_tds_amount`,
                `tsi`.`custom_total_tds_amount` AS `custom_total_tds_amount`,
                `tsi`.`custom_total_disallowance_amount` AS `custom_total_disallowance_amount`,
                `tsi`.`custom_total_settled_amount` AS `custom_total_settled_amount`,
                `tsi`.`custom_total_writeoff_amount` AS `custom_total_writeoff_amount`,
                `tsi`.`custom_total_amount_number_card` AS `custom_total_amount_number_card`,
                `tsi`.`custom_file_upload` AS `custom_file_upload`,
                `tsi`.`custom_transform` AS `custom_transform`,
                `tsi`.`custom_index` AS `custom_index`,
                `tsi`.`custom_ignore_for_ob` AS `custom_ignore_for_ob`
            from
                (`tabSales Invoice` `tsi`
            join `tabYearly Due` `tyd`)
            where
                `tsi`.`posting_date` <= '2024-03-31'
                and `tyd`.`fiscal_year` = '2023-2024'
                and `tyd`.`parent` = `tsi`.`name`
                and `tsi`.`status` <> 'Cancelled'
                and `tyd`.`due_amount` >= 0.000000001
                and `tsi`.`custom_ignore_for_ob` <> 1;
            """)
        
    def sales_invoice_total_breakup_view(self):
        frappe.db.sql("""
            CREATE OR REPLACE VIEW `viewSales Invoice Total Breakup` AS
            select
                `vsicy`.`name` AS `bill_number`,
                `vsicy`.`posting_date` AS `bill_date`,
                `vsicy`.`rounded_total` AS `current_claim_amount`,
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
                `vsicy`.`custom_ma_claim_id` AS `ma_claim_id`,
                `vsicy`.`custom_mrn` AS `mrn`
            from
                (`tabSales Invoice` `vsicy`
            left join `viewSettlement Summary Total` `vss` on
                (`vsicy`.`name` = `vss`.`bill_number`));
                """)
        
    def create_sales_invoice_with_reference_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSales Invoice With Reference` AS
            select
                `vsirwrn`.`Bill Number` AS `Bill Number`,
                `vsirwrn`.`Bill Date` AS `Bill Date`,
                `vsirwrn`.`Entity` AS `Entity`,
                `vsirwrn`.`Region` AS `Region`,
                `vsirwrn`.`Branch` AS `Branch`,
                `vsirwrn`.`Branch Type` AS `Branch Type`,
                `vsirwrn`.`Customer` AS `Customer`,
                `vsirwrn`.`Customer Group` AS `Customer Group`,
                `vsirwrn`.`Claim ID` AS `Claim ID`,
                `vsirwrn`.`MA Claim ID` AS `MA Claim ID`,
                `vsirwrn`.`Patient Name` AS `Patient Name`,
                `vsirwrn`.`MRN` AS `MRN`,
                `vsirwrn`.`Status` AS `Status`,
                `vsirwrn`.`Insurance Name` AS `Insurance Name`,
                `vsirwrn`.`Claim Amount` AS `Claim Amount`,
                `vsirwrn`.`Total Settled Amount` AS `Total Settled Amount`,
                `vsirwrn`.`Total TDS Amount` AS `Total TDS Amount`,
                `vsirwrn`.`Total Disallowance Amount` AS `Total Disallowance Amount`,
                `vsirwrn`.`Outstanding Amount` AS `Outstanding Amount`,
                `vsirwrn`.`Entry Type` AS `Entry Type`,
                `vsirwrn`.`Entry Name` AS `Entry Name`,
                `vsirwrn`.`Settled Amount` AS `Settled Amount`,
                `vsirwrn`.`TDS Amount` AS `TDS Amount`,
                `vsirwrn`.`Disallowed Amount` AS `Disallowed Amount`,
                `vsirwrn`.`Allocated Amount` AS `Allocated Amount`,
                `vsirwrn`.`UTR Date` AS `UTR Date`,
                `vsirwrn`.`UTR Number` AS `UTR Number`,
                `vsirwrn`.`Payment Posting Date` AS `Payment Posting Date`,
                `vsirwrn`.`Payment Created Date` AS `Payment Created Date`,
                `vsirwrn`.`Match Logic` AS `Match Logic`,
                `vsirwrn`.`Settlement Advice` AS `Settlement Advice`,
                `vsirwrn`.`row_count` AS `row_count`,
                `tbt`.`bank_account` AS `Bank Account (Reference)`,
                `tbt`.`custom_entity` AS `Bank Entity (Reference)`,
                `tbt`.`custom_region` AS `Bank Region (Reference)`
            from
                (`viewSales Invoice Report 24-25 with Row Number` `vsirwrn`
            left join `tabBank Transaction` `tbt` on
                (`tbt`.`custom_cg_utr_number` = `vsirwrn`.`UTR Number`));
            """)
    
    def create_settlement_summary_view(Self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSettlement Summary` AS
            select
                `T`.`bill_number` AS `bill_number`,
                sum(`T`.`settled`) AS `settled`,
                sum(`T`.`tds`) AS `tds`,
                sum(`T`.`disallowance`) AS `disallowance`
            from
                (
                select
                    `vpes`.`bill_number` AS `bill_number`,
                    `vpes`.`settled` AS `settled`,
                    `vpes`.`tds` AS `tds`,
                    `vpes`.`disallowance` AS `disallowance`
                from
                    `viewPayment Entry Summary` `vpes`
            union
                select
                    `vjes`.`bill_number` AS `bill_number`,
                    0 AS `settled`,
                    `vjes`.`tds` AS `tds`,
                    `vjes`.`disallowance` AS `disallowance`
                from
                    `viewJournal Entry Summary` `vjes`) `T`
            group by
                `T`.`bill_number`;
            """)
        
    def create_settlement_summary_total_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSettlement Summary Total` AS
            select
                `T`.`bill_number` AS `bill_number`,
                sum(`T`.`settled`) AS `settled`,
                sum(`T`.`tds`) AS `tds`,
                sum(`T`.`disallowance`) AS `disallowance`
            from
                (
                select
                    `vpes`.`bill_number` AS `bill_number`,
                    `vpes`.`settled` AS `settled`,
                    `vpes`.`tds` AS `tds`,
                    `vpes`.`disallowance` AS `disallowance`
                from
                    `viewPayment Entry Summary Total` `vpes`
            union
                select
                    `vjes`.`bill_number` AS `bill_number`,
                    0 AS `settled`,
                    `vjes`.`tds` AS `tds`,
                    `vjes`.`disallowance` AS `disallowance`
                from
                    `viewJournal Entry Summary Total` `vjes`) `T`
            group by
                `T`.`bill_number`;
            """)
        
    def create_sorted_current_bank_transaction_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewSorted Current Brank Transaction` AS
            select
    `cbt`.`Entity` AS `Entity`,
    `cbt`.`Region` AS `Region`,
    `cbt`.`Party_Group` AS `Party_Group`,
    `cbt`.`Insurance` AS `Insurance`,
    `cbt`.`UTR_Number` AS `UTR_Number`,
    `cbt`.`UTR_Date` AS `UTR_Date`,
    `cbt`.`Current_Allocated_Amount` AS `Current_Allocated_Amount`,
    `cbt`.`Current_UnAllocated` AS `Current_UnAllocated`,
    `cbt`.`Current_Deposit` AS `Current_Deposit`,
    `cbt`.`Branch_Type` AS `Branch_Type`,
    `cbt`.`Status` AS `Status`,
    `cbt`.`Bank_Account` AS `Bank_Account`,
    `cbt`.`NS_Ledger_Code` AS `NS_Ledger_Code`,
    `cbt`.`Description` AS `Description`,
    `cbt`.`Reference_Number` AS `Reference_Number`,
    `cbt`.`Internal_Id` AS `Internal_Id`,
    `cbt`.`Based_On` AS `Based_On`,
    `cbt`.`Allocated_Amount(Payment_Entries)` AS `Allocated_Amount(Payment_Entries)`,
    `cbt`.`Payment_Document(Payment_Entries)` AS `Payment_Document(Payment_Entries)`,
    `cbt`.`Payment_Entry(Payment_Entries)` AS `Payment_Entry(Payment_Entries)`,
    `cbt`.`Bill_Region(Payment_Entries)` AS `Bill_Region(Payment_Entries)`,
    `cbt`.`Creation_Date(Payment_Entries)` AS `Creation_Date(Payment_Entries)`,
    `cbt`.`Posting_Date(Payment_Entries)` AS `Posting_Date(Payment_Entries)`,
    `cbt`.`Bill_Date(Payment_Entries)` AS `Bill_Date(Payment_Entries)`,
    `cbt`.`Bill_Branch(Payment_Entries)` AS `Bill_Branch(Payment_Entries)`,
    `cbt`.`Bill_Entity(Payment_Entries)` AS `Bill_Entity(Payment_Entries)`,
    `cbt`.`Bill_Branch_Type(Payment_Entries)` AS `Bill_Branch_Type(Payment_Entries)`,
    row_number() over ( partition by `cbt`.`Reference_Number`
order by
    `cbt`.`Reference_Number`) AS `row_count`
from
    `Dragarwals-db-Prod`.`current_bank_transaction` `cbt`
where
    `cbt`.`Current_Deposit` > 0;
            """)
        
    def create_cancelled_bills_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewcancelled_bills` AS
            select
                `tsi`.`name` AS `name`,
                `tsi`.`creation` AS `creation`,
                `tsi`.`modified` AS `modified`,
                `tsi`.`modified_by` AS `modified_by`,
                `tsi`.`owner` AS `owner`,
                `tsi`.`docstatus` AS `docstatus`,
                `tsi`.`idx` AS `idx`,
                `tsi`.`title` AS `title`,
                `tsi`.`bill_no` AS `bill_no`,
                `tsi`.`naming_series` AS `naming_series`,
                `tsi`.`customer` AS `customer`,
                `tsi`.`customer_name` AS `customer_name`,
                `tsi`.`tax_id` AS `tax_id`,
                `tsi`.`company` AS `company`,
                `tsi`.`company_tax_id` AS `company_tax_id`,
                `tsi`.`posting_date` AS `posting_date`,
                `tsi`.`posting_time` AS `posting_time`,
                `tsi`.`set_posting_time` AS `set_posting_time`,
                `tsi`.`due_date` AS `due_date`,
                `tsi`.`is_pos` AS `is_pos`,
                `tsi`.`pos_profile` AS `pos_profile`,
                `tsi`.`is_consolidated` AS `is_consolidated`,
                `tsi`.`is_return` AS `is_return`,
                `tsi`.`return_against` AS `return_against`,
                `tsi`.`update_billed_amount_in_sales_order` AS `update_billed_amount_in_sales_order`,
                `tsi`.`is_debit_note` AS `is_debit_note`,
                `tsi`.`amended_from` AS `amended_from`,
                `tsi`.`cost_center` AS `cost_center`,
                `tsi`.`project` AS `project`,
                `tsi`.`currency` AS `currency`,
                `tsi`.`conversion_rate` AS `conversion_rate`,
                `tsi`.`selling_price_list` AS `selling_price_list`,
                `tsi`.`price_list_currency` AS `price_list_currency`,
                `tsi`.`plc_conversion_rate` AS `plc_conversion_rate`,
                `tsi`.`ignore_pricing_rule` AS `ignore_pricing_rule`,
                `tsi`.`scan_barcode` AS `scan_barcode`,
                `tsi`.`update_stock` AS `update_stock`,
                `tsi`.`set_warehouse` AS `set_warehouse`,
                `tsi`.`set_target_warehouse` AS `set_target_warehouse`,
                `tsi`.`total_qty` AS `total_qty`,
                `tsi`.`total_net_weight` AS `total_net_weight`,
                `tsi`.`base_total` AS `base_total`,
                `tsi`.`base_net_total` AS `base_net_total`,
                `tsi`.`total` AS `total`,
                `tsi`.`net_total` AS `net_total`,
                `tsi`.`tax_category` AS `tax_category`,
                `tsi`.`taxes_and_charges` AS `taxes_and_charges`,
                `tsi`.`shipping_rule` AS `shipping_rule`,
                `tsi`.`incoterm` AS `incoterm`,
                `tsi`.`named_place` AS `named_place`,
                `tsi`.`base_total_taxes_and_charges` AS `base_total_taxes_and_charges`,
                `tsi`.`total_taxes_and_charges` AS `total_taxes_and_charges`,
                `tsi`.`base_grand_total` AS `base_grand_total`,
                `tsi`.`base_rounding_adjustment` AS `base_rounding_adjustment`,
                `tsi`.`base_rounded_total` AS `base_rounded_total`,
                `tsi`.`base_in_words` AS `base_in_words`,
                `tsi`.`grand_total` AS `grand_total`,
                `tsi`.`rounding_adjustment` AS `rounding_adjustment`,
                `tsi`.`use_company_roundoff_cost_center` AS `use_company_roundoff_cost_center`,
                `tsi`.`rounded_total` AS `rounded_total`,
                `tsi`.`in_words` AS `in_words`,
                `tsi`.`total_advance` AS `total_advance`,
                `tsi`.`outstanding_amount` AS `outstanding_amount`,
                `tsi`.`disable_rounded_total` AS `disable_rounded_total`,
                `tsi`.`apply_discount_on` AS `apply_discount_on`,
                `tsi`.`base_discount_amount` AS `base_discount_amount`,
                `tsi`.`is_cash_or_non_trade_discount` AS `is_cash_or_non_trade_discount`,
                `tsi`.`additional_discount_account` AS `additional_discount_account`,
                `tsi`.`additional_discount_percentage` AS `additional_discount_percentage`,
                `tsi`.`discount_amount` AS `discount_amount`,
                `tsi`.`other_charges_calculation` AS `other_charges_calculation`,
                `tsi`.`total_billing_hours` AS `total_billing_hours`,
                `tsi`.`total_billing_amount` AS `total_billing_amount`,
                `tsi`.`cash_bank_account` AS `cash_bank_account`,
                `tsi`.`base_paid_amount` AS `base_paid_amount`,
                `tsi`.`paid_amount` AS `paid_amount`,
                `tsi`.`base_change_amount` AS `base_change_amount`,
                `tsi`.`change_amount` AS `change_amount`,
                `tsi`.`account_for_change_amount` AS `account_for_change_amount`,
                `tsi`.`allocate_advances_automatically` AS `allocate_advances_automatically`,
                `tsi`.`only_include_allocated_payments` AS `only_include_allocated_payments`,
                `tsi`.`write_off_amount` AS `write_off_amount`,
                `tsi`.`base_write_off_amount` AS `base_write_off_amount`,
                `tsi`.`write_off_outstanding_amount_automatically` AS `write_off_outstanding_amount_automatically`,
                `tsi`.`write_off_account` AS `write_off_account`,
                `tsi`.`write_off_cost_center` AS `write_off_cost_center`,
                `tsi`.`redeem_loyalty_points` AS `redeem_loyalty_points`,
                `tsi`.`loyalty_points` AS `loyalty_points`,
                `tsi`.`loyalty_amount` AS `loyalty_amount`,
                `tsi`.`loyalty_program` AS `loyalty_program`,
                `tsi`.`loyalty_redemption_account` AS `loyalty_redemption_account`,
                `tsi`.`loyalty_redemption_cost_center` AS `loyalty_redemption_cost_center`,
                `tsi`.`customer_address` AS `customer_address`,
                `tsi`.`address_display` AS `address_display`,
                `tsi`.`contact_person` AS `contact_person`,
                `tsi`.`contact_display` AS `contact_display`,
                `tsi`.`contact_mobile` AS `contact_mobile`,
                `tsi`.`contact_email` AS `contact_email`,
                `tsi`.`territory` AS `territory`,
                `tsi`.`shipping_address_name` AS `shipping_address_name`,
                `tsi`.`shipping_address` AS `shipping_address`,
                `tsi`.`dispatch_address_name` AS `dispatch_address_name`,
                `tsi`.`dispatch_address` AS `dispatch_address`,
                `tsi`.`company_address` AS `company_address`,
                `tsi`.`company_address_display` AS `company_address_display`,
                `tsi`.`ignore_default_payment_terms_template` AS `ignore_default_payment_terms_template`,
                `tsi`.`payment_terms_template` AS `payment_terms_template`,
                `tsi`.`tc_name` AS `tc_name`,
                `tsi`.`terms` AS `terms`,
                `tsi`.`po_no` AS `po_no`,
                `tsi`.`po_date` AS `po_date`,
                `tsi`.`debit_to` AS `debit_to`,
                `tsi`.`party_account_currency` AS `party_account_currency`,
                `tsi`.`is_opening` AS `is_opening`,
                `tsi`.`unrealized_profit_loss_account` AS `unrealized_profit_loss_account`,
                `tsi`.`against_income_account` AS `against_income_account`,
                `tsi`.`sales_partner` AS `sales_partner`,
                `tsi`.`amount_eligible_for_commission` AS `amount_eligible_for_commission`,
                `tsi`.`commission_rate` AS `commission_rate`,
                `tsi`.`total_commission` AS `total_commission`,
                `tsi`.`letter_head` AS `letter_head`,
                `tsi`.`group_same_items` AS `group_same_items`,
                `tsi`.`select_print_heading` AS `select_print_heading`,
                `tsi`.`language` AS `language`,
                `tsi`.`from_date` AS `from_date`,
                `tsi`.`auto_repeat` AS `auto_repeat`,
                `tsi`.`to_date` AS `to_date`,
                `tsi`.`status` AS `status`,
                `tsi`.`inter_company_invoice_reference` AS `inter_company_invoice_reference`,
                `tsi`.`campaign` AS `campaign`,
                `tsi`.`represents_company` AS `represents_company`,
                `tsi`.`source` AS `source`,
                `tsi`.`customer_group` AS `customer_group`,
                `tsi`.`is_internal_customer` AS `is_internal_customer`,
                `tsi`.`is_discounted` AS `is_discounted`,
                `tsi`.`remarks` AS `remarks`,
                `tsi`.`repost_required` AS `repost_required`,
                `tsi`.`_user_tags` AS `_user_tags`,
                `tsi`.`_comments` AS `_comments`,
                `tsi`.`_assign` AS `_assign`,
                `tsi`.`_liked_by` AS `_liked_by`,
                `tsi`.`_seen` AS `_seen`,
                `tsi`.`custom_bill_no` AS `custom_bill_no`,
                `tsi`.`region` AS `region`,
                `tsi`.`branch` AS `branch`,
                `tsi`.`branch_type` AS `branch_type`,
                `tsi`.`entity` AS `entity`,
                `tsi`.`custom_insurance_name` AS `custom_insurance_name`,
                `tsi`.`update_billed_amount_in_delivery_note` AS `update_billed_amount_in_delivery_note`,
                `tsi`.`dont_create_loyalty_points` AS `dont_create_loyalty_points`,
                `tsi`.`custom_mrn` AS `custom_mrn`,
                `tsi`.`custom_claim_id` AS `custom_claim_id`,
                `tsi`.`total_outstanding_amount` AS `total_outstanding_amount`,
                `tsi`.`custom_ma_claim_id` AS `custom_ma_claim_id`,
                `tsi`.`custom_patient_name` AS `custom_patient_name`,
                `tsi`.`custom_payer_name` AS `custom_payer_name`,
                `tsi`.`sales_status1` AS `sales_status1`,
                `tsi`.`custom_year` AS `custom_year`,
                `tsi`.`custom_month` AS `custom_month`,
                `tsi`.`update_outstanding_for_self` AS `update_outstanding_for_self`,
                `tsi`.`custom_tds_amount` AS `custom_tds_amount`,
                `tsi`.`custom_total_tds_amount` AS `custom_total_tds_amount`,
                `tsi`.`custom_total_disallowance_amount` AS `custom_total_disallowance_amount`,
                `tsi`.`custom_total_settled_amount` AS `custom_total_settled_amount`,
                `tsi`.`custom_total_writeoff_amount` AS `custom_total_writeoff_amount`,
                `tsi`.`custom_total_amount_number_card` AS `custom_total_amount_number_card`,
                `tsi`.`custom_file_upload` AS `custom_file_upload`,
                `tsi`.`custom_transform` AS `custom_transform`,
                `tsi`.`custom_index` AS `custom_index`,
                `tsi`.`custom_ignore_for_ob` AS `custom_ignore_for_ob`,
                `tsi`.`custom_patient_age` AS `custom_patient_age`,
                `tb`.`name` AS `bill_name`
            from
                (`tabSales Invoice` `tsi`
            join `tabBill` `tb` on
                (`tb`.`mrn` = `tsi`.`custom_mrn`))
            where
                `tb`.`status` = 'CANCELLED';
            """)
        
    def create_cumulative_bank_report_chacklist_view(self):
        # Created viewcumulative_bank_report_checklist to get the cumulative values in current year bank report
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewcumulative_bank_report_checklist` AS
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
        
    def create_cumulative_current_year_sales_invoice_view(self):
        
        # Created viewcumulative_current_year_sales_invoice
        # : Total TDS/Total Disallowance/Total Settled = Total of TDS/Disallowance/Settled

        frappe.db.sql("""CREATE OR REPLACE VIEW `viewcumulative_current_year_sales_invoice` AS
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
        
    def create_cumulative_current_year_sales_invoice_with_job_view(self):
        # Created viewcumulative_current_year_sales_invoice_with_job view it contains cumulative values with job ID
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewcumulative_current_year_sales_invoice_with_job` AS
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
            join `tabPayment Entry` `tpe` on
                (`tpe`.`name` = `tfr`.`record`))
            join `viewcumulative_current_year_sales_invoice` `vcysi` on
                (`tpe`.`custom_sales_invoice` = `vcysi`.`Bill Number`))
            group by
                `tfr`.`job`;
            """)
        
    def create_current_bank_report_checklist_view(self):
        # Created viewcurrent_bank_report_checklist - to get the difference of Total Deposit - (Total Allocated + Total Un-allocated) < 9
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewcurrent_bank_report_checklist` AS
            select
                `tfr`.`job` AS `job`,
                case
                    when `vscbt`.`row_count` = 1 then `vscbt`.`UTR_Number`
                    else NULL
                end AS `UTR`,
                case
                    when `vscbt`.`row_count` = 1 then `vscbt`.`Current_Allocated_Amount`
                    else NULL
                end AS `Allocated Amount`,
                case
                    when `vscbt`.`row_count` = 1 then `vscbt`.`Current_UnAllocated`
                    else NULL
                end AS `Un-Allocated Amount`,
                case
                    when `vscbt`.`row_count` = 1 then `vscbt`.`Current_Deposit`
                    else NULL
                end AS `Deposit`,
                case
                    when `vscbt`.`row_count` = 1 then `vscbt`.`Current_Deposit` - (`vscbt`.`Current_Allocated_Amount` + `vscbt`.`Current_UnAllocated`)
                    else NULL
                end AS `diff`
            from
                ((`tabFile Records` `tfr`
            join `tabPayment Entry` `tpe` on
                (`tpe`.`name` = `tfr`.`record`))
            join `viewSorted Current Brank Transaction` `vscbt` on
                (`vscbt`.`UTR_Number` = `tpe`.`reference_no`))
            having
                `UTR` is not null
            order by
                `vscbt`.`row_count`;
            """)
        
    def create_current_year_si_checklist_view(self):
        # Created viewSales Invoice Current Year Breakup : Total Claim Amount - ( Total Settled + Total TDS + Total Disallowance ) < 9
            frappe.db.sql("""CREATE OR REPLACE VIEW `viewcurrent_year_si_checklist` AS
                select
                    `vsicyb`.`bill_number` AS `bill_number`,
                    `tfr`.`job` AS `job`,
                    `vsicyb`.`current_claim_amount` AS `claim_amount`,
                    `vsicyb`.`outstanding_amount` AS `outstanding_amount`,
                    `vsicyb`.`settled_amount` AS `settled_amount`,
                    `vsicyb`.`tds_amount` AS `tds_amount`,
                    `vsicyb`.`disallowed_amount` AS `disallowed_amount`,
                    `vsicyb`.`current_claim_amount` - (`vsicyb`.`settled_amount` + `vsicyb`.`tds_amount` + `vsicyb`.`disallowed_amount` + `vsicyb`.`outstanding_amount`) AS `diff`
                from
                    ((`tabFile Records` `tfr`
                join `tabPayment Entry` `tpe` on
                    (`tpe`.`name` = `tfr`.`record`))
                join `viewSales Invoice Current Year Breakup` `vsicyb` on
                    (`vsicyb`.`bill_number` = `tpe`.`custom_sales_invoice`));
                      """)

    def create_bill_tracker_latest_view(self):
        frappe.db.sql("""CREATE OR REPLACE VIEW `viewBillTracker` AS
                    SELECT tbt.* ,tsi.region as 'region', tsi.branch as 'branch', tsi.posting_date as 'Bill Date'
                    FROM `tabBill Tracker` tbt join `tabSales Invoice` tsi on tsi.name = tbt.parent
                    WHERE (tbt.parent, tbt.date) IN (
                        SELECT parent, MAX(date)
                        FROM `tabBill Tracker`
                        GROUP BY parent
                    );
        """)

    def create_viewmatcher(self):
        frappe.db.sql("""
        CREATE OR REPLACE VIEW `viewMatcher` AS
        select
            `tm`.`sales_invoice` AS `sales_invoice`,
            `tm`.`settlement_advice` AS `settlement_advice`,
            `tm`.`match_logic` AS `match_logic`,
            `tm`.`bank_transaction` AS `bank_transaction`
        from
            (`Dragarwals-db-Prod`.`tabMatcher` `tm`
        join `Dragarwals-db-Prod`.`tabPayment Entry` `tpe` on
            (`tm`.`sales_invoice` = `tpe`.`custom_sales_invoice`
                and `tm`.`bank_transaction` = `tpe`.`reference_no`))
        where
            `tpe`.`posting_date` > '2024-03-31'
            and `tpe`.`status` <> 'Cancelled';
        """)
    
    def process(self):
        self.create_file_upload_mail_view()
        self.create_file_upload_view()
        self.create_staging_view()
        self.create_advice_view()
        self.create_matcher_view()
        self.create_payment_entry_view()
        self.create_collection_view()
        self.create_current_bank_transaction_view()
        self.create_current_sales_invoice_view()
        self.create_sales_invoice_report_view()
        self.create_journal_entry_24_25_view()
        self.create_journal_entry_summary_view()
        self.create_journal_entry_summary_total()
        self.create_journal_entry_total()
        self.create_matcher_total_view()
        self.create_payment_entry_24_25_view()
        self.create_payment_entry_summary_view()
        self.create_payment_entry_summary_total_view()
        self.create_payment_entry_total_view()
        self.create_sales_invoice_balance_view()
        self.create_sales_invoice_summary_view()
        self.create_sales_invoice_current_year_view()
        self.create_settlement_summary_view()
        self.create_sales_invoice_current_year_breakup_view()
        self.create_sales_invoice_payers_remark_view()
        self.create_sales_invoice_reference_24_25_view()
        self.create_sales_invoice_reference_total_view()
        self.create_sales_invoice_report_24_25_view()
        self.create_sales_invoice_report_24_25_with_row_number_view()
        self.create_settlement_summary_total_view()
        self.sales_invoice_total_breakup_view()
        self.create_sales_invoice_report_total_view()
        self.create_sales_invoice_report_total_with_row_number_view()
        self.create_sorted_current_bank_transaction_view()
        self.create_cancelled_bills_view()
        self.create_cumulative_bank_report_chacklist_view()
        self.create_cumulative_current_year_sales_invoice_view()
        self.create_cumulative_current_year_sales_invoice_with_job_view()
        self.create_current_bank_report_checklist_view()
        self.create_current_year_si_checklist_view()
        self.create_sales_invoice_with_reference_view()
        self.create_bill_tracker_latest_view()
        self.create_viewmatcher()
        
def execute():
    ViewInstance = ViewCreator()
    ViewInstance.process()