import frappe
from agarwals.utils.updater import update_bill_no_separate_column, update_utr_in_separate_column
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error

class Matcher:
    def add_log_error(self, doctype, name, error):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name',doctype)
        error_log.set('reference_name', name)
        error_log.save()
       
    def update_payment_order(self, matcher_record, record):
        matcher_record.set("payment_order", record['payment_order'])
        return matcher_record

    def update_matcher_amount(self, matcher_record, record):
        matcher_record.set("settled_amount", record['settled_amount'])
        matcher_record.set("tds_amount", record['tds_amount'])
        matcher_record.set('disallowance_amount',record['disallowed_amount'])
        return matcher_record

    def get_matcher_name(self, _prefix, _suffix):
        return _prefix + "-" + _suffix

    def update_advice_status(self, sa_name, status, msg):
        frappe.db.set_value('Settlement Advice', sa_name, 'status', status)
        frappe.db.set_value('Settlement Advice', sa_name, 'remark', msg)
        frappe.db.commit()

    def create_matcher_record(self, matcher_records):
        if not len(matcher_records):
            return

        for record in matcher_records:
            if record['sa']:
                if record.status not in ('Open', 'Not Processed'):
                    continue
                if frappe.get_value('Sales Invoice', record['bill'], 'status') == "Cancelled":
                    self.update_advice_status(record['sa'], 'Warning', 'Cancelled Bill')
                    continue

            matcher_record = frappe.new_doc("Matcher")
            matcher_record.set('sales_invoice', record['bill']) # Bill Is Mandatory

            if record['cb']:
                matcher_record.set('claimbook', record['cb'])
                matcher_record.set('insurance_company_name', record['insurance_name'])

                if record['logic'] == 'MA3-CN': # Only for the ClaimBook Operation
                    matcher_record = self.update_matcher_amount(matcher_record, record)
                    matcher_record = self.update_payment_order(matcher_record, record)

            if record['sa']:
                matcher_record.set('settlement_advice', record['sa'])

                if record.payment_order:
                    matcher_record = self.update_payment_order(matcher_record, record)
                matcher_record = self.update_matcher_amount(matcher_record, record)
                frappe.db.commit()
                
            if record['bank']:
                matcher_record.set('bank_transaction', record['bank'])
                matcher_record.set('name', self.get_matcher_name(record['bill'], record['bank']))
            else:
                if record['cb']:
                    matcher_record.set('name', self.get_matcher_name(record['bill'], record['cb']))
                else:
                    matcher_record.set('name', self.get_matcher_name(record['bill'], record['cb']))
                    
            matcher_record.set('match_logic', record['logic'])
            matcher_record.set('status', 'Open')

            try:
                matcher_record.save()
                frappe.db.set_value('Settlement Advice', record['sa'], 'status', 'Not Processed')
                frappe.db.set_value('Settlement Advice', record['sa'], 'matcher_id', matcher_record.name)

            except Exception as e:
                self.update_advice_status(record, 'Error', str(e))
                self.add_log_error('Matcher', matcher_record.name, str(e))
                
        frappe.db.commit()

    def delete_other_entries(self):
        match_logic = ('MA5-BN', 'MA3-CN', 'MA1-CN') # Important Tag
        frappe.db.sql("""Update `tabSettlement Advice` SET status = 'Open' where status = 'Not Processed'""")
        frappe.db.sql("""Delete from `tabMatcher` where match_logic not in %(match_logic)s""" , values = {'match_logic' : match_logic})
        frappe.db.commit()

    def process(self):
        self.delete_other_entries()
        update_utr_in_separate_column()
        update_bill_no_separate_column()
        
        ma5_bn = """
                SELECT
                bi.name as bill,
                '' as cb,
                sa.name as sa,
                bt.name as bank,
                '' as insurance_name,
                sa.settled_amount as settled_amount,
                sa.tds_amount as tds_amount,
                sa.disallowed_amount as disallowed_amount,
                "MA5-BN" as logic,
                1 as payment_order,
                sa.status as status
                FROM
                    `tabBank Transaction` bt
                JOIN
                    `tabSettlement Advice` sa
                    ON (sa.cg_utr_number = bt.custom_cg_utr_number 
                    OR sa.cg_formatted_utr_number = bt.custom_cg_utr_number)
                JOIN
                    `tabBill` bi
                    ON sa.cg_formatted_bill_number = bi.cg_formatted_bill_number
                LEFT JOIN
                    `tabMatcher` mt
                    ON CONCAT(bi.name, "-", bt.name) = mt.name
                WHERE
                    mt.name IS NULL
                    AND sa.status = 'Open';
                """

        ma5_bn_records = frappe.db.sql(ma5_bn, as_dict=True)
        if ma5_bn_records: self.create_matcher_record(ma5_bn_records)

        ma1_cn = """
                SELECT
                bi.name as bill,
                cb.name as cb,
                sa.name as sa,
                bt.name as bank,
                cb.insurance_company_name as insurance_name,
                sa.settled_amount as settled_amount,
                sa.tds_amount as tds_amount,
                sa.disallowed_amount as disallowed_amount,
                "MA1-CN" as logic,
                2 as payment_order,
                sa.status as status
                FROM
                    `tabBank Transaction` bt
                JOIN
                    `tabSettlement Advice` sa
                    ON (sa.cg_utr_number = bt.custom_cg_utr_number 
                    OR sa.cg_formatted_utr_number = bt.custom_cg_utr_number)
                JOIN
                    `tabClaimBook` cb
                    ON (sa.claim_key is not null and (cb.al_key = sa.claim_key or cb.cl_key = sa.claim_key))
                JOIN
                    `tabBill` bi
                    ON ((bi.claim_key is not null and (bi.claim_key = cb.al_key or bi.claim_key = cb.cl_key))
                    OR (bi.ma_claim_key is not null and (bi.ma_claim_key = cb.al_key or bi.ma_claim_key = cb.cl_key)))
                    and (cb.cg_formatted_bill_number is not null and (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number))
                LEFT JOIN
                    `tabMatcher` mt
                    ON CONCAT(bi.name, "-", bt.name) = mt.name
                WHERE
                    mt.name IS NULL
                    AND sa.status = 'Open';
                """
        
        ma1_cn_records = frappe.db.sql(ma1_cn, as_dict=True)
        if ma1_cn_records: self.create_matcher_record(ma1_cn_records)
		    
        ma3_cn = """
                SELECT
                bi.name as bill,
                cb.name as cb,
                '' as sa,
                bt.name as bank,
                cb.insurance_company_name as insurance_name,
                "MA3-CN" as logic,
                cb.settled_amount as settled_amount,
                cb.tds_amount as tds_amount,
                0 as disallowed_amount,
                3 as payment_order
                FROM
                    `tabBank Transaction` bt
                JOIN   
                    `tabClaimBook` cb
                    ON (cb.cg_utr_number = bt.custom_cg_utr_number or cb.cg_formatted_utr_number = bt.custom_cg_utr_number )
                JOIN
                    `tabBill` bi
                    ON ((bi.claim_key is not null and (bi.claim_key = cb.al_key or bi.claim_key = cb.cl_key))
                    or (bi.ma_claim_key is not null and (bi.ma_claim_key = cb.al_key or bi.ma_claim_key = cb.cl_key)))
                    and (cb.cg_formatted_bill_number is not null and (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number))
                LEFT JOIN
                    `tabMatcher` mt
                    ON CONCAT(bi.name, "-", bt.name) = mt.name
                WHERE
                    mt.name IS NULL
                """

        ma3_cn_records = frappe.db.sql(ma3_cn, as_dict=True)
        if ma3_cn_records: self.create_matcher_record(ma3_cn_records)
			
        ma1_bn = """SELECT
                    bi.name as bill,
                    cb.name as cb,
                    sa.name as sa,
                    bt.name as bank,
                    cb.insurance_company_name as insurance_name,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA1-BN" as logic,
                    sa.status as status
                FROM
                    `tabBank Transaction` bt
                JOIN
                    `tabSettlement Advice` sa
                    ON (sa.cg_utr_number = bt.custom_cg_utr_number 
                    OR sa.cg_formatted_utr_number = bt.custom_cg_utr_number)
                JOIN
                    `tabClaimBook` cb
                    ON (sa.claim_key is not null and (cb.al_key = sa.claim_key or cb.cl_key = sa.claim_key))
                JOIN
                    `tabBill` bi
                    ON (cb.cg_formatted_bill_number is not null and (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number))
                LEFT JOIN
                    `tabMatcher` mt
                    ON bi.name = mt.sales_invoice AND mt.match_logic = 'MA1-CN'
                WHERE
                    mt.sales_invoice IS NULL
                    AND sa.status = 'Open';
                """
        ma1_bn_records = frappe.db.sql(ma1_bn, as_dict=True)
        if ma1_bn_records: self.create_matcher_record(ma1_bn_records)

        ma5_cn = """SELECT
                    bi.name as bill,
                    '' as cb,
                    sa.name as sa,
                    bt.name as bank,
                    '' as insurance_name,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA5-CN" as logic
                FROM
                    `tabBank Transaction` bt
                JOIN
                    `tabSettlement Advice` sa
                    ON (sa.cg_utr_number = bt.custom_cg_utr_number 
                    OR sa.cg_formatted_utr_number = bt.custom_cg_utr_number)
                JOIN
                    `tabBill` bi
                    ON (sa.claim_key = bi.claim_key 
                    OR sa.claim_key = bi.ma_claim_key)
                LEFT JOIN
                    `tabMatcher` mt
                    ON CONCAT(bi.name, '-', bt.name) = mt.name
                WHERE
                    mt.name IS NULL
                    AND sa.status = 'Open'
            """
        ma5_cn_records = frappe.db.sql(ma5_cn, as_dict=True)
        if ma5_cn_records: self.create_matcher_record(ma5_cn_records)

        ma2_cn = """SELECT
                    bi.name as bill,
                    cb.name as cb,
                    sa.name as sa,
                    '' as bank,
                    cb.insurance_company_name as insurance_name,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA2-CN" as logic
                FROM
                    `tabClaimBook` cb
                JOIN
                    `tabSettlement Advice` sa
                    ON (cb.al_key = sa.claim_key OR cb.cl_key = sa.claim_key)
                JOIN
                    `tabBill` bi
                    ON ((bi.claim_key IS NOT NULL AND (bi.claim_key = cb.al_key OR bi.claim_key = cb.cl_key))
                    OR (bi.ma_claim_key IS NOT NULL AND (bi.ma_claim_key = cb.al_key OR bi.ma_claim_key = cb.cl_key)))
                    AND (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number)
                LEFT JOIN
                    `tabMatcher` mt
                    ON bi.name = mt.sales_invoice
                WHERE
                    mt.sales_invoice IS NULL
                    AND sa.status = 'Open';
         """

        ma2_cn_records = frappe.db.sql(ma2_cn, as_dict=True)
        if ma2_cn_records: self.create_matcher_record(ma2_cn_records)

        ma2_bn = """SELECT
                    bi.name as bill,
                    cb.name as cb,
                    sa.name as sa,
                    '' as bank,
                    cb.insurance_company_name as insurance_name,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA2-BN" as logic
                FROM
                    `tabClaimBook` cb
                JOIN
                    `tabSettlement Advice` sa
                    ON (cb.al_key = sa.claim_key OR cb.cl_key = sa.claim_key)
                JOIN
                    `tabBill` bi
                    ON bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
                LEFT JOIN
                    `tabMatcher` mt
                    ON bi.name = mt.sales_invoice
                WHERE
                    mt.sales_invoice IS NULL
                    AND sa.status = 'Open';
         """
        ma2_bn_records = frappe.db.sql(ma2_bn, as_dict=True)
        if ma2_bn_records: self.create_matcher_record(ma2_bn_records)

        ma3_bn = """SELECT
                bi.name as bill,
                cb.name as cb,
                '' as sa,
                bt.name as bank,
                cb.insurance_company_name as insurance_name,
                "MA3-BN" as logic
            FROM
                `tabBank Transaction` bt
            JOIN
                `tabClaimBook` cb
                ON (cb.cg_utr_number = bt.custom_cg_utr_number 
                OR cb.cg_formatted_utr_number = bt.custom_cg_utr_number)
            JOIN
                `tabBill` bi
                ON bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
            LEFT JOIN
                `tabMatcher` mt
                ON CONCAT(bi.name, '-', bt.name) = mt.name
            WHERE
                mt.name IS NULL
         """
        ma3_bn_records = frappe.db.sql(ma3_bn, as_dict=True)
        if ma3_bn_records: self.create_matcher_record(ma3_bn_records)

        ma4_cn = """SELECT
                    bi.name as bill,
                    cb.name as cb,
                    '' as sa,
                    '' as bank,
                    cb.insurance_company_name as insurance_name,
                    "MA4-CN" as logic
                    FROM
                        `tabClaimBook` cb
                    JOIN
                        `tabBill` bi
                        ON ((bi.claim_key = cb.al_key OR bi.claim_key = cb.cl_key) 
                        OR (bi.ma_claim_key = cb.al_key OR bi.ma_claim_key = cb.cl_key))
                        AND bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
                    LEFT JOIN
                        `tabMatcher` mt
                        ON bi.name = mt.sales_invoice
                    WHERE
                        mt.sales_invoice IS NULL
                """

        ma4_cn_records = frappe.db.sql(ma4_cn, as_dict=True)
        if ma4_cn_records: self.create_matcher_record(ma4_cn_records)

        ma4_bn = """SELECT
                    bi.name as bill,
                    cb.name as cb,
                    '' as sa,
                    '' as bank,
                    cb.insurance_company_name as insurance_name,
                    "MA4-BN" as logic
                    FROM
                        `tabClaimBook` cb
                    JOIN
                        `tabBill` bi
                        ON bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
                    LEFT JOIN
                        `tabMatcher` mt
                        ON bi.name = mt.sales_invoice
                    WHERE
                        mt.sales_invoice IS NULL
                """

        ma4_bn_records = frappe.db.sql(ma4_bn, as_dict=True)
        if ma4_bn_records: self.create_matcher_record(ma4_bn_records)

        ma6_cn = """
                SELECT
                    bi.name as bill,
                    '' as cb,
                    '' as bank,
                    sa.name as sa,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA6-CN" as logic
                FROM
                    `tabSettlement Advice` sa
                JOIN
                    `tabBill` bi
                    ON (sa.claim_key = bi.claim_key OR sa.claim_key = bi.ma_claim_key)
                LEFT JOIN
                    `tabMatcher` mt
                    ON bi.name = mt.sales_invoice
                WHERE
                    mt.sales_invoice IS NULL
                    AND sa.status = 'Open';
                """

        ma6_cn_records = frappe.db.sql(ma6_cn, as_dict=True)
        if ma6_cn_records: self.create_matcher_record(ma6_cn_records)

        ma6_bn = """SELECT
                    bi.name as bill,
                    '' as cb,
                    sa.name as sa,
                    '' as bank,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA6-BN" as logic
                FROM
                    `tabSettlement Advice` sa
                JOIN
                    `tabBill` bi
                    ON sa.cg_formatted_bill_number = bi.cg_formatted_bill_number
                LEFT JOIN
                    `tabMatcher` mt
                    ON bi.name = mt.sales_invoice
                WHERE
                    mt.sales_invoice IS NULL
                    AND sa.status = 'Open';
            """
        ma6_bn_records = frappe.db.sql(ma6_bn, as_dict=True)
        if ma6_bn_records: self.create_matcher_record(ma6_bn_records)

@frappe.whitelist()
def update_matcher():
    #frappe.enqueue(Matcher().process(), queue = "long", is_async = True,  job_name = "matcher_batch_process" , timeout = 25000 )
    Matcher().process()


# Intially, the settlement Advice M.Status is Open
# Then, for unmatched part is Unmatched 
# Then, for matched 
# We have to clear the Unmatched as Settlement Advices
# @frappe.whitelist()
# def process(args):
#     try:
#         args=cast_to_dic(args)
#         chunk_doc = chunk.create_chunk(args["step_id"])
#         chunk.update_status(chunk_doc, "InProgress")
#         try:
#             update_utr_in_separate_column()
#             update_bill_no_separate_column()
#             Matcher().process()
#             chunk.update_status(chunk_doc, "Processed")
#         except Exception as e:
#             chunk.update_status(chunk_doc, "Error")
#     except Exception as e:
#         chunk_doc = chunk.create_chunk(args["step_id"])
#         chunk.update_status(chunk_doc, "Error")
#         log_error(e,'Step')