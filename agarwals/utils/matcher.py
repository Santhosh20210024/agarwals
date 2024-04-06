import frappe
from agarwals.utils.updater import update_bill_no_separate_column, update_utr_in_separate_column


class Matcher:
    def log_error(self,doctype, name, error):
        error_log = frappe.new_doc('Matcher Error Log')
        error_log.set('reference_doctype',doctype)
        error_log.set('reference_name', name)
        error_log.set('error',error)
        error_log.save()

    def insert_into_matcher_table(self,records):
        for record in records:
            if record['sa']:
                if record.matcher_status:
                    if record.matcher_status != 'Open':
                        continue
            matcher_record = frappe.new_doc("Matcher")
            matcher_record.set('sales_invoice',record['bill'])
            if record['cb']:
                matcher_record.set('claimbook',record['cb'])
                matcher_record.set('insurance_company_name',record['insurance_name'])
                if record['logic'] == 'MA3-CN':
                    matcher_record.set("settled_amount", record['settled_amount'])
                    matcher_record.set("tds_amount", record['tds_amount'])
                
            if record['sa']:
                 if record.payment_order:
                      matcher_record.set('payment_order', record['payment_order'])
                 matcher_record.set('settlement_advice',record['sa'])
                 matcher_record.set('settled_amount', record['settled_amount'])
                 matcher_record.set('tds_amount', record['tds_amount'])
                 matcher_record.set('disallowance_amount',record['disallowed_amount'])
                 frappe.db.set_value('Settlement Advice', record['sa'], 'matcher_status', 'Processed' )
                 frappe.db.commit()
                
            if record['bank']:
                matcher_record.set('bank_transaction', record['bank'])
                matcher_record.set('name', record['bill'] + "-" + record['bank'])
                
            else:
                if record['cb']:
                    matcher_record.set('name', record['bill'] + "-" + record['cb'])
                else:
                    matcher_record.set('name', record['bill'] + "-" + record['sa'])
                    
            matcher_record.set('match_logic',record['logic'])
            try:
                matcher_record.save()
            except Exception as e:
                self.log_error('Matcher',matcher_record.name,e)
                
        frappe.db.commit()

    def process(self):
        ma5_bn = """select
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
            sa.matcher_status as matcher_status
        from
        	`tabBank Transaction` bt,
        	`tabSettlement Advice` sa,
        	`tabBill` bi
        where
        	(sa.cg_utr_number = bt.custom_cg_utr_number
        		or sa.cg_formatted_utr_number = bt.custom_cg_utr_number )
        	and sa.cg_formatted_bill_number  = bi.cg_formatted_bill_number 
        	and CONCAT(bi.name,'-',bt.name) not in (SELECT name FROM `tabMatcher`)
            and bi.status != 'Cancelled'
            """
        
        ma5_bn_records = frappe.db.sql(ma5_bn, as_dict=True)
        
        print("______________________________________________________________MA5-BN_________________________________________________")
        if ma5_bn_records:
            self.insert_into_matcher_table(ma5_bn_records)
        
        ma1_cn = """
            select
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
            sa.matcher_status as matcher_status
        from
	        `tabBank Transaction` bt,
	        `tabSettlement Advice` sa,
	        `tabClaimBook` cb,
	        `tabBill` bi
        where
	        (sa.cg_utr_number = bt.custom_cg_utr_number
		        or sa.cg_formatted_utr_number = bt.custom_cg_utr_number )
	        and (cb.al_key = sa.claim_key
		        or cb.cl_key = sa.claim_key)
	        and (((bi.claim_key = cb.al_key or bi.claim_key = cb.cl_key) or (bi.ma_claim_key = cb.al_key or bi.ma_claim_key = cb.cl_key)) and (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number))
	        and CONCAT(bi.name,'-',bt.name) not in (SELECT name FROM `tabMatcher`)
            and bi.status != 'Cancelled'
           """
        
        ma1_cn_records = frappe.db.sql(ma1_cn,as_dict=True)
        print("______________________________________________________________MA1-CN_________________________________________________")
        if ma1_cn_records:
            self.insert_into_matcher_table(ma1_cn_records)
            
		      
        ma3_cn = """select
	        bi.name as bill,
	        cb.name as cb,
	        '' as sa,
	        bt.name as bank,
	        cb.insurance_company_name as insurance_name,
	        "MA3-CN" as logic,
            cb.settled_amount as settled_amount,
            cb.tds_amount as tds_amount,
            3 as payment_order
        from
	        `tabBank Transaction` bt,
	        `tabClaimBook` cb,
	        `tabBill` bi
        where
	        (cb.cg_utr_number = bt.custom_cg_utr_number
		        or cb.cg_formatted_utr_number = bt.custom_cg_utr_number )
	        and (((bi.claim_key = cb.al_key or bi.claim_key = cb.cl_key) or (bi.ma_claim_key = cb.al_key or bi.ma_claim_key = cb.cl_key)) and (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number))
	        and CONCAT(bi.name,'-',bt.name) not in (SELECT name FROM `tabMatcher`)
            and bi.status != 'Cancelled'
         """
        ma3_cn_records = frappe.db.sql(ma3_cn, as_dict=True)
        
        print("______________________________________________________________MA3-CN_________________________________________________")
        if ma3_cn_records:
            self.insert_into_matcher_table(ma3_cn_records)
			
        ma1_bn = """select
	        bi.name as bill,
	        cb.name as cb,
	        sa.name as sa,
	        bt.name as bank,
	        cb.insurance_company_name as insurance_name,
	        sa.settled_amount as settled_amount,
	        sa.tds_amount as tds_amount,
	        sa.disallowed_amount as disallowed_amount,
	        "MA1-BN" as logic
        from
	        `tabBank Transaction` bt,
        	`tabSettlement Advice` sa,
	        `tabClaimBook` cb,
	        `tabBill` bi
        where
	        (sa.cg_utr_number = bt.custom_cg_utr_number
		        or sa.cg_formatted_utr_number = bt.custom_cg_utr_number )
	        and (cb.al_key = sa.claim_key
		        or cb.cl_key = sa.claim_key)
	        and bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
	        and bi.name not in (SELECT sales_invoice FROM `tabMatcher` WHERE match_logic = 'MA1-CN') 
	        and CONCAT(bi.name,'-',bt.name) not in (SELECT name FROM `tabMatcher`)
            and bi.status != 'Cancelled'
            """
        ma1_bn_records = frappe.db.sql(ma1_bn, as_dict=True)
        
        print(
            "______________________________________________________________MA1-BN_________________________________________________")
        if ma1_bn_records:
            self.insert_into_matcher_table(ma1_bn_records)

        ma5_cn = """select
	        bi.name as bill,
	        '' as cb,
	        sa.name as sa,
	        bt.name as bank,
	        '' as insurance_name,
	        sa.settled_amount as settled_amount,
	        sa.tds_amount as tds_amount,
	        sa.disallowed_amount as disallowed_amount,
	        "MA5-CN" as logic
        from
	        `tabBank Transaction` bt,
	        `tabSettlement Advice` sa,
	        `tabBill` bi
        where
	        (sa.cg_utr_number = bt.custom_cg_utr_number
		        or sa.cg_formatted_utr_number = bt.custom_cg_utr_number )
	        and ((sa.claim_key  = bi.claim_key) or (sa.claim_key = bi.ma_claim_key) )
	        and CONCAT(bi.name,'-',bt.name) not in (SELECT name FROM `tabMatcher`)
            and bi.status != 'Cancelled'
            """
        ma5_cn_records = frappe.db.sql(ma5_cn, as_dict=True)
        
        print(
            "______________________________________________________________MA5-CN_________________________________________________")
        if ma5_cn_records:
            self.insert_into_matcher_table(ma5_cn_records)

        ma2_cn = """select
        	bi.name as bill,
        	cb.name as cb,
        	sa.name as sa,
        	'' as bank,
        	cb.insurance_company_name as insurance_name,
        	sa.settled_amount as settled_amount,
        	sa.tds_amount as tds_amount,
        	sa.disallowed_amount as disallowed_amount,
        	"MA2-CN" as logic
        from
        	`tabClaimBook` cb,
        	`tabSettlement Advice` sa,
        	`tabBill` bi
        where
        	(cb.al_key = sa.claim_key or cb.cl_key = sa.claim_key)
        	and (((bi.claim_key = cb.al_key or bi.claim_key = cb.cl_key) or (bi.ma_claim_key = cb.al_key or bi.ma_claim_key = cb.cl_key)) and (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number))
        	and bi.name not in (SELECT sales_invoice FROM `tabMatcher`)
            and bi.status != 'Cancelled'
         """

        ma2_cn_records = frappe.db.sql(ma2_cn, as_dict=True)
        print(
            "______________________________________________________________MA2-CN_________________________________________________")
        if ma2_cn_records:
            self.insert_into_matcher_table(ma2_cn_records)

        ma2_bn = """select
        	bi.name as bill,
        	cb.name as cb,
        	sa.name as sa,
        	'' as bank,
        	cb.insurance_company_name  as insurance_name,
        	sa.settled_amount as settled_amount,
        	sa.tds_amount as tds_amount,
        	sa.disallowed_amount as disallowed_amount,
        	"MA2-BN" as logic
        from
        	`tabClaimBook` cb,
        	`tabSettlement Advice` sa,
        	`tabBill` bi
        where
        	(cb.al_key = sa.claim_key or cb.cl_key = sa.claim_key)
        	and bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
        	and bi.name not in (SELECT sales_invoice FROM `tabMatcher`)
            and bi.status != 'Cancelled'
         """
        ma2_bn_records = frappe.db.sql(ma2_bn, as_dict=True)
        print(
            "______________________________________________________________MA2-BN_________________________________________________")
        if ma2_bn_records:
            self.insert_into_matcher_table(ma2_bn_records)

        ma3_bn = """select
	        bi.name as bill,
	        cb.name as cb,
	        '' as sa,
	        bt.name as bank,
	        cb.insurance_company_name as insurance_name,
	        "MA3-BN" as logic
        from
	        `tabBank Transaction` bt,
	        `tabClaimBook` cb,
	        `tabBill` bi
        where
	        (cb.cg_utr_number = bt.custom_cg_utr_number
		        or cb.cg_formatted_utr_number = bt.custom_cg_utr_number )
	        and bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
	        and CONCAT(bi.name,'-',bt.name) not in (SELECT name FROM `tabMatcher`)
            and bi.status != 'Cancelled'
         """
        ma3_bn_records = frappe.db.sql(ma3_bn, as_dict=True)
        print(
            "______________________________________________________________MA3-BN_________________________________________________")
        if ma3_bn_records:
            self.insert_into_matcher_table(ma3_bn_records)

        ma4_cn = """select
	        bi.name as bill,
	        cb.name as cb,
	        '' as sa,
	        '' as bank,
	        cb.insurance_company_name as insurance_name,
	        "MA4-CN" as logic
        from
	        `tabClaimBook` cb,
	        `tabBill` bi
        where
	        (((bi.claim_key = cb.al_key or bi.claim_key = cb.cl_key) or (bi.ma_claim_key = cb.al_key or bi.ma_claim_key = cb.cl_key)) and (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number))
	        and bi.name not in (SELECT sales_invoice FROM `tabMatcher`)
            and bi.status != 'Cancelled'
            """

        ma4_cn_records = frappe.db.sql(ma4_cn, as_dict=True)
        print(
            "______________________________________________________________MA4-CN_________________________________________________")
        if ma4_cn_records:
            self.insert_into_matcher_table(ma4_cn_records)

        ma4_bn = """select
	        bi.name as bill,
	        cb.name as cb,
	        '' as sa,
	        '' as bank,
	        cb.insurance_company_name as insurance_name,
	        "MA4-BN" as logic
        from
	        `tabClaimBook` cb,
	        `tabBill` bi
        where
	        bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
	        and bi.name not in (SELECT sales_invoice FROM `tabMatcher`)
            and bi.status != 'Cancelled'
         """

        ma4_bn_records = frappe.db.sql(ma4_bn, as_dict=True)
        print(
            "______________________________________________________________MA4-BN_________________________________________________")
        if ma4_bn_records:
            self.insert_into_matcher_table(ma4_bn_records)

		# settlement advice
        ma6_cn = """select
	        bi.name as bill,
	        '' as cb,
	        '' as bank,
	        sa.name as sa,
	        sa.settled_amount as settled_amount,
	        sa.tds_amount as tds_amount,
	        sa.disallowed_amount as disallowed_amount,
	        "MA6-CN" as logic
        from
	        `tabSettlement Advice` sa,
	        `tabBill` bi
        where
	        (sa.claim_key = bi.claim_key or sa.claim_key = bi.ma_claim_key)
	        and bi.name not in (SELECT sales_invoice FROM `tabMatcher`)
            and bi.status != 'Cancelled'
         """
        ma6_cn_records = frappe.db.sql(ma6_cn, as_dict=True)
        
        print(
            "______________________________________________________________MA6-CN_________________________________________________")
        if ma6_cn_records:
            self.insert_into_matcher_table(ma6_cn_records)

        ma6_bn = """select
	        bi.name as bill,
	        '' as cb,
	        sa.name as sa,
	        '' as bank,
	        sa.settled_amount as settled_amount,
	        sa.tds_amount as tds_amount,
	        sa.disallowed_amount as disallowed_amount,
	        "MA6-BN" as logic
        from
	        `tabSettlement Advice` sa,
	        `tabBill` bi
        where
	        sa.cg_formatted_bill_number  = bi.cg_formatted_bill_number 
	        and bi.name not in (SELECT sales_invoice FROM `tabMatcher`)
            and bi.status != 'Cancelled'
         """
        ma6_bn_records = frappe.db.sql(ma6_bn, as_dict=True)
        print(
            "______________________________________________________________MA6-BN_________________________________________________")
        if ma6_bn_records:
            self.insert_into_matcher_table(ma6_bn_records)
        print("END____________________________________________________________________")

@frappe.whitelist()
def update_matcher():
    update_utr_in_separate_column()
    update_bill_no_separate_column()
    Matcher().process()
