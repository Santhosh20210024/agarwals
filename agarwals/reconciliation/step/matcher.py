import frappe
from agarwals.utils.updater import update_bill_no_separate_column, update_utr_in_separate_column
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from agarwals.utils.index_update import update_index
from agarwals.utils.error_handler import log_error as error_handler

class Matcher:
    def add_log_error(self, doctype, name, error):
        if len(name)>=140:
            name = name[0:130]
        if len(error)>=140:
            error = error[0:139]
        error_handler(error=error, doc=doctype, doc_name=name)

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
                if frappe.get_value('Sales Invoice', record['bill'], 'status') == "CANCELLED":
                    self.update_advice_status(record['sa'], 'Warning', 'Cancelled Bill')
                    continue
                if frappe.get_value('Sales Invoice', record['bill'], 'status') == "CANCELLED AND DELETED":
                    self.update_advice_status(record['sa'], 'Warning', 'Cancelled and deleted Bill')
                    continue

            matcher_record = frappe.new_doc("Matcher")
            matcher_record.set('sales_invoice', record['bill']) # Bill Is Mandatory

            if record['cb']:
                if frappe.get_value('Sales Invoice', record['bill'], 'status') == "CANCELLED":
                    continue
                if frappe.get_value('Sales Invoice', record['bill'], 'status') == "CANCELLED AND DELETED":
                    continue
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
                    matcher_record.set('name', self.get_matcher_name(record['bill'], record['sa']))
                    
            matcher_record.set('match_logic', record['logic'])
            matcher_record.set('status', 'Open')

            try:
                matcher_record.save()
                if record['sa']:
                    update_query = """
                                    UPDATE `tabSettlement Advice`
                                    SET status = %(status)s, matcher_id = %(matcher_id)s
                                    WHERE name = %(name)s
                                """
                    frappe.db.sql(update_query, values = { 'status' : 'Not Processed', 'matcher_id' : matcher_record.name, 'name': matcher_record.settlement_advice})
                    frappe.db.commit()

            except Exception as e:
                if record['sa']:
                    update_query = """
                                        UPDATE `tabSettlement Advice`
                                        SET status = %(status)s, remark = %(remark)s
                                        WHERE name = %(name)s
                                    """
                    frappe.db.sql(update_query, values = { 'status' : 'Warning', 'remark' : str(e), 'name': matcher_record.settlement_advice})
                    frappe.db.commit()
                self.add_log_error('Matcher', matcher_record.name, str(e))
                
        frappe.db.commit()

    def delete_other_entries(self):
        match_logic = ('MA5-BN', 'MA3-CN', 'MA1-CN') # Important Tag
        frappe.db.sql("""Delete from `tabMatcher` where match_logic not in %(match_logic)s""" , values = {'match_logic' : match_logic})
        frappe.db.sql("""Update `tabSettlement Advice` SET status = 'Open', remark = NULL where status = 'Not Processed'""")
        frappe.db.sql("""Update `tabSettlement Advice` SET status = 'Open', remark = NULL where remark in ( 'Check the bill number', 'Bill Number Not Found')""")
        frappe.db.commit()
    
    
    def update_validate_entries(self):
        update_query = """
            UPDATE `tabSettlement Advice` tsa LEFT JOIN `tabSales Invoice` tsi on tsa.bill_no = tsi.name SET tsa.status = 'Warning', tsa.remark = 'Check the bill number' 
            WHERE tsi.name is NULL and tsa.status = 'Open'
        """
        frappe.db.sql(update_query, values = { 'status' : 'Warning', 'remark' : 'Check the bill number'})

        update_query = """
                        UPDATE `tabSettlement Advice`
                        SET status = %(status)s, remark = %(remark)s
                        WHERE (bill_no is null or bill_no ='')
                    """
        frappe.db.sql(update_query, values = { 'status' : 'Warning', 'remark' : 'Bill Number Not Found'})
        frappe.db.commit()

    
    def execute_cursors(self, query_list):
        for query_item in query_list:
            chunk_size = 10000
            while True:
                print(query_item)
                query = f"{query_item} LIMIT {chunk_size}"
                records = frappe.db.sql(query, as_dict = True)
                if len(records) == 0:
                    break
                
                self.create_matcher_record(records)
        self.update_validate_entries()
        
    def process(self):
        update_index() 
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
                    AND sa.status = 'Open'
                """

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
                    AND sa.status = 'Open'
                """

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
                    ON CONCAT(bi.name, "-", bt.name) = mt.name
                WHERE
                    mt.name IS NULL
                    AND sa.status = 'Open'
                """

        ma5_cn = """SELECT
                    bi.name as bill,
                    '' as cb,
                    sa.name as sa,
                    bt.name as bank,
                    '' as insurance_name,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA5-CN" as logic,
                    sa.status as status
                FROM
                    `tabBank Transaction` bt
                JOIN `tabSettlement Advice` sa ON
                    (sa.cg_utr_number = bt.custom_cg_utr_number
                        OR sa.cg_formatted_utr_number = bt.custom_cg_utr_number)
                JOIN `tabBill` bi ON
                    (sa.claim_key = bi.claim_key
                        OR sa.claim_key = bi.ma_claim_key)
                WHERE
                    sa.status = 'Open'
                """
        
        ma2_cn = """SELECT
                    bi.name as bill,
                    cb.name as cb,
                    sa.name as sa,
                    '' as bank,
                    cb.insurance_company_name as insurance_name,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA2-CN" as logic,
                    sa.status as status
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
                    ON CONCAT(bi.name, '-', cb.name) = mt.name
                WHERE
                    mt.name is null
                    AND sa.status = 'Open'
         """
        ma2_bn = """SELECT
                    bi.name as bill,
                    cb.name as cb,
                    sa.name as sa,
                    '' as bank,
                    cb.insurance_company_name as insurance_name,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA2-BN" as logic,
                    sa.status as status
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
                    ON CONCAT(bi.name, '-', cb.name) = mt.name
                WHERE
                        mt.name is null
                        AND sa.status = 'Open'
         """

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
        
        ma6_cn = """
                SELECT
                    bi.name as bill,
                    '' as cb,
                    '' as bank,
                    sa.name as sa,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA6-CN" as logic,
                    sa.status as status
                FROM
                    `tabSettlement Advice` sa
                JOIN
                    `tabBill` bi
                    ON (sa.claim_key = bi.claim_key OR sa.claim_key = bi.ma_claim_key)
                LEFT JOIN
                    `tabMatcher` mt
                    ON CONCAT(bi.name, '-', sa.name) = mt.name
                WHERE
                    mt.name is null
                    AND sa.status = 'Open'
                """
        
        ma6_bn = """SELECT
                    bi.name as bill,
                    '' as cb,
                    sa.name as sa,
                    '' as bank,
                    sa.settled_amount as settled_amount,
                    sa.tds_amount as tds_amount,
                    sa.disallowed_amount as disallowed_amount,
                    "MA6-BN" as logic,
                    sa.status as status
                FROM
                    `tabSettlement Advice` sa
                JOIN
                    `tabBill` bi
                    ON sa.cg_formatted_bill_number = bi.cg_formatted_bill_number
                LEFT JOIN
                    `tabMatcher` mt
                    ON CONCAT(bi.name, '-', sa.name) = mt.name
                WHERE
                    mt.name is null
                    AND sa.status = 'Open'
            """
        
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
                    ON CONCAT(bi.name, '-', cb.name) = mt.name and bi.name = mt.sales_invoice
                    WHERE
                        mt.name is null
                        AND mt.sales_invoice is null
                """

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
                    ON CONCAT(bi.name, '-', cb.name) = mt.name and bi.name = mt.sales_invoice
                    WHERE
                        mt.name is null
                        AND mt.sales_invoice is null
                 """


        query_list = [ma1_cn, ma5_bn, ma3_cn, ma1_bn, ma5_cn, ma2_cn, ma2_bn, ma6_cn, ma6_bn, ma3_bn, ma4_cn, ma4_bn]
        self.execute_cursors(query_list)

@frappe.whitelist()
def update_matcher():
    Matcher().process()

@frappe.whitelist()
def process(args):
    try:
        args=cast_to_dic(args)
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "InProgress")
        try:
            Matcher().process()
            chunk.update_status(chunk_doc, "Processed")
            frappe.msgprint("Processed")
        except Exception as e:
            chunk.update_status(chunk_doc, "Error")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        log_error(e,'Step')
