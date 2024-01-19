import frappe

@frappe.whitelist()
def get_outstanding_amount():
    outstanding_amount = frappe.db.sql("""
                                    SELECT ABS( t1.collection - t2.revenue ) AS `Amount`
                                    FROM (
                                    select sum(deposit) as collection from `tabBank Transaction` tbt ) AS t1,
                                    (
                                    select sum(total) as revenue  from `tabSales Invoice` tsi where tsi.status != 'Cancelled'
                                    ) AS t2;
                                    """, as_dict = True)

    return {
        "value" : outstanding_amount[0]['Amount'],
        "fieldtype" : "Currency",
        "ignore_user_permissions" : 1
    }

# @frappe.whitelist()
# def get_revenue():
#     revenue_amount = frappe.db.sql("""
#                                       SELECT SUM(t1.total) as `Revenue` 
#                                       FROM `tabSales Invoice` t1 where t1.status != 'Cancelled';
#                                       """, as_dict = True)
#     return {
#         "value" : revenue_amount[0]['Revenue'],
#         "fieldtype" : "Currency"
#     }

# # @frappe.