def get_matcher_query(matcher_pattern):
    queries = {
        "MA1-CN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            cb.name as claim,
            sa.name as advice,
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
                ON bt.custom_utr_key = sa.utr_key
            JOIN 
                `tabClaimBook Claim Key` cck
                ON sa.claim_key = cck.claim_key
            JOIN
                `tabClaimBook` cb
                ON cb.name = cck.claimbook
            JOIN 
                `tabBill Claim Key` bck
                ON bck.claim_key = cck.claim_key
            JOIN
                `tabBill` bi
                ON (bi.name = bck.bill and (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number))
            LEFT JOIN
                `tabMatcher` mt
                ON CONCAT(bi.name, "-", bt.name) = mt.name
            WHERE
                mt.name IS NULL
                AND sa.status = 'Open' and bt.custom_utr_key != 'IGNORED'
        """,
        "MA1-BN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            cb.name as claim,
            sa.name as advice,
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
                 ON bt.custom_utr_key = sa.utr_key
            JOIN 
                `tabClaimBook Claim Key` cck
                ON sa.claim_key = cck.claim_key
            JOIN
                `tabClaimBook` cb
                ON cb.name = cck.claimbook
            JOIN
                `tabBill` bi
                ON bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
            LEFT JOIN
                `tabMatcher` mt
                ON CONCAT(bi.name, "-", bt.name) = mt.name
            WHERE
                mt.name IS NULL
                AND sa.status = 'Open' and bt.custom_utr_key != 'IGNORED'
        """,
        "MA2-CN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            cb.name as claim,
            sa.name as advice,
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
                `tabClaimBook Claim Key` cck
                ON cb.name = cck.claimbook
            JOIN
                `tabSettlement Advice` sa
                ON cck.claim_key = sa.claim_key
            JOIN
                 `tabBill Claim Key`  bck
                 ON bck.claim_key = cck.claim_key
            JOIN
                `tabBill` bi
                ON bi.name = bck.bill
                AND (bi.cg_formatted_bill_number = cb.cg_formatted_bill_number)
            LEFT JOIN
                `tabMatcher` mt
                ON bi.name = mt.sales_invoice 
            WHERE
                mt.name is null
                AND sa.status = 'Open' and sa.utr_key != 'IGNORED'
        """,
        "MA2-BN": """
             SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            cb.name as claim,
            sa.name as advice,
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
                `tabClaimBook Claim Key` cck
                ON cb.name = cck.claimbook
            JOIN
                `tabSettlement Advice` sa
                ON cck.claim_key = sa.claim_key
            JOIN
                `tabBill` bi
                ON bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
            LEFT JOIN
                `tabMatcher` mt
                ON bi.name = mt.sales_invoice 
            WHERE
                mt.name is null
                AND sa.status = 'Open' and sa.utr_key != 'IGNORED'
        """,
        "MA3-CN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            cb.name as claim,
            '' as advice,
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
                ON cb.utr_key = bt.custom_utr_key
            JOIN
                `tabClaimBook Claim Key` cck 
                ON cck.claimbook = cb.name
            JOIN 
                `tabBill Claim Key` bck
                ON bck.claim_key = cck.claim_key
            JOIN
                `tabBill` bi
                ON bi.name = bck.bill
                and bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
            LEFT JOIN
                `tabMatcher` mt
                ON CONCAT(bi.name, "-", bt.name) = mt.name
            WHERE
                mt.name IS NULL and bt.custom_utr_key != 'IGNORED'
        """,
        "MA3-BN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            cb.name as claim,
            '' as advice,
            bt.name as bank,
            cb.insurance_company_name as insurance_name,
            cb.settled_amount as settled_amount,
            cb.tds_amount as tds_amount,
            0 as disallowed_amount,
            "MA3-BN" as logic
            FROM
                `tabBank Transaction` bt
            JOIN
                `tabClaimBook` cb
                ON cb.utr_key = bt.custom_utr_key
            JOIN
                `tabBill` bi
                ON bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
            LEFT JOIN
                `tabMatcher` mt
                ON CONCAT(bi.name, '-', bt.name) = mt.name
            WHERE
                mt.name IS NULL and bt.custom_utr_key != 'IGNORED'
        """,
        "MA4-CN": """
            SELECT
            bi.name as bill,
            cb.name as claim,
            bi.claim_amount as claim_amount,
            '' as advice,
            '' as bank,
            cb.insurance_company_name as insurance_name,
            cb.settled_amount as settled_amount,
            cb.tds_amount as tds_amount,
            0 as disallowed_amount,
            "MA4-CN" as logic
            FROM
                `tabClaimBook` cb
            JOIN
                `tabClaimBook Claim Key` cck
                ON cck.claimbook = cb.name	                        
            JOIN 	                  
                `tabBill Claim Key` bck	                        
                ON bck.claim_key = cck.claim_key
            JOIN
                `tabBill` bi
                ON (bi.name = bck.bill
                AND bi.cg_formatted_bill_number = cb.cg_formatted_bill_number)
            LEFT JOIN
            `tabMatcher` mt
            ON bi.name = mt.sales_invoice
            WHERE mt.name is null and cb.utr_key != 'IGNORED'
        """,
        "MA4-BN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            cb.name as claim,
            '' as advice,
            '' as bank,
            cb.insurance_company_name as insurance_name,
            cb.settled_amount as settled_amount,
            cb.tds_amount as tds_amount,
            0 as disallowed_amount,
            "MA4-BN" as logic
            FROM
                `tabClaimBook` cb
            JOIN
                `tabBill` bi
                ON bi.cg_formatted_bill_number = cb.cg_formatted_bill_number
            LEFT JOIN
            `tabMatcher` mt 
            ON bi.name = mt.sales_invoice
            WHERE mt.name is null and cb.utr_key != 'IGNORED'
        """,
        "MA5-CN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            '' as claim,
            sa.name as advice,
            bt.name as bank,
            '' as insurance_name,
            sa.settled_amount as settled_amount,
            sa.tds_amount as tds_amount,
            sa.disallowed_amount as disallowed_amount,
            "MA5-CN" as logic,
            sa.status as status
            FROM
                `tabBank Transaction` bt
            JOIN `tabSettlement Advice` sa 
                ON  sa.utr_key = bt.custom_utr_key
            JOIN 
                `tabBill Claim Key` bck
                ON bck.claim_key = sa.claim_key
            JOIN 
               `tabBill` bi 
                ON (bi.name = bck.bill AND sa.cg_formatted_bill_number = bi.cg_formatted_bill_number)
            LEFT JOIN 
	            `tabMatcher` mt
	            ON CONCAT(bi.name, "-", bt.name) = mt.name
            WHERE
             	mt.name is null and
                sa.status = 'Open' and bt.custom_utr_key != 'IGNORED'
        """,
        "MA5-BN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            '' as claim,
            sa.name as advice,
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
                ON sa.utr_key = bt.custom_utr_key
            JOIN
                `tabBill` bi
                ON sa.cg_formatted_bill_number = bi.cg_formatted_bill_number
            LEFT JOIN
                `tabMatcher` mt
                ON CONCAT(bi.name, "-", bt.name) = mt.name
            WHERE
                mt.name IS NULL
                AND sa.status = 'Open' and bt.custom_utr_key != 'IGNORED'
        """,
        "MA6-CN": """
            SELECT
            bi.name as bill,
            bi.claim_amount as claim_amount,
            '' as claim,
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
                `tabBill Claim Key` bck 
                ON sa.claim_key = bck.claim_key
            JOIN
                `tabBill` bi
                ON bi.name = bck.bill
            LEFT JOIN
                `tabMatcher` mt
                ON bi.name = mt.sales_invoice
            WHERE
                mt.name is null
                AND sa.status = 'Open' and and sa.utr_key != 'IGNORED'
        """,
        "MA6-BN": """
            SELECT
		    bi.name as bill,
		    bi.claim_amount as claim_amount,
		    '' as claim,
		    sa.name as advice,
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
		        ON bi.name = mt.sales_invoice
		    WHERE
		        mt.name is null
		        AND sa.status = 'Open' and and sa.utr_key != 'IGNORED'
        """
    }

    return queries.get(matcher_pattern)
