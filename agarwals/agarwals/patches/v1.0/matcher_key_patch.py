import frappe


def delete_matcher_records():
	frappe.db.sql("""DELETE from `tabMatcher` where status = 'Error'""")


def update_advice_status():
	frappe.db.sql("""UPDATE `tabSettlement Advice` tsa left join `tabMatcher` tma on tsa.name = tma.settlement_advice set tsa.status = 'Unmatched' where tsa.name is null""")
	frappe.db.sql("""UPDATE `tabSettlement Advice` status = 'Warning' where status = 'Error' and name in (select settlement_advice from `tabMatcher`)""")

# Error
# Open
# Not Processed
# Partially Processed
# Fully Processed
# Warning
# Unmatched
def execute():
    # 1 Patch
    update_advice_status()
    delete_matcher_records()
    

	# for doctype in ("Sales Order Item", "Bin"):
	# 	frappe.reload_doctype(doctype)

	# repost_for = frappe.db.sql(
	# 	"""
	# 	select
	# 		distinct item_code, warehouse
	# 	from
	# 		(
	# 			(
	# 				select distinct item_code, warehouse
	# 							from `tabSales Order Item` where docstatus=1
	# 			) UNION (
	# 				select distinct item_code, warehouse
	# 				from `tabPacked Item` where docstatus=1 and parenttype='Sales Order'
	# 			)
	# 		) so_item
	# 	where
	# 		exists(select name from tabItem where name=so_item.item_code and ifnull(is_stock_item, 0)=1)
	# """
	# )

	# for item_code, warehouse in repost_for:
	# 	if not (item_code and warehouse):
	# 		continue
	# 	update_bin_qty(item_code, warehouse, {"reserved_qty": get_reserved_qty(item_code, warehouse)})

	# frappe.db.sql(
	# 	"""delete from tabBin
	# 	where exists(
	# 		select name from tabItem where name=tabBin.item_code and ifnull(is_stock_item, 0) = 0
	# 	)
	# """
	# )
