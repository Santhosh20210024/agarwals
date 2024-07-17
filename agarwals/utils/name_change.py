import frappe

def test():
    try:
        all_jv = frappe.get_all("Journal Entry", {"name": ["like", "%JV%"]}, "*")
        for jv in all_jv:
            jv_account_list = frappe.get_all("Journal Entry Account", filters={"parent": jv.name}, fields="*")
            for jv_account in jv_account_list:
                if jv_account.account == "Write Off - A":
                    new_name = f"{jv.custom_sales_invoice}-WO"
                elif jv_account.account == "WriteBack - A":
                    reference = jv.remark
                    utr_name = reference.split(" ")
                    utr_name = utr_name[1]
                    utr_name = utr_name[1:]
                    new_name = f"{utr_name}-WB"
            if not new_name:
                new_doc = frappe.new_doc("Error Record Log")
                new_doc.error_message = f"{jv.name} not in wb or wo"
                new_doc.save()
                continue
            frappe.rename_doc("Journal Entry", jv.name, new_name)
            frappe.db.commit()
            frappe.msgprint("test1")

    except Exception as e:
        new_doc = frappe.new_doc("Error Record Log")
        new_doc.error_message = f"{jv.name} not in wb or wo,{e}"
        new_doc.save()
        frappe.db.commit()

@frappe.whitelist()
def check_doc():
    all_jv = frappe.get_all("Journal Entry", {"name": ["like", "%JV%"]}, "*")
    for i in range(0, len(all_jv), 100):
        frappe.enqueue("test", queue="long", all_jv=all_jv[i:i + 100])
