import frappe

@frappe.whitelist()
def custom_prepared_report():
    try:
        control_panel = frappe.get_single("Control Panel")
        report_list = control_panel.prepared_report_list
        if isinstance(report_list, str):
            prepared_report_list = [item.strip() for item in report_list.split(',')]
        else:
            raise ValueError("Report list should be a comma-separated string.")

        site_url = frappe.utils.get_url()
        if prepared_report_list:
            for report_name in prepared_report_list:
                filtered_reports = frappe.get_all(
                    "Prepared Report",
                    filters={
                        "report_name": report_name,
                        "status": "completed",
                        "custom_flag": 0
                    },
                    fields=["name"]
                )
                if filtered_reports:
                    full_url = f"{site_url}/app/query-report/{report_name}/?prepared_report_name={filtered_reports[0].name}"
                    print("full_url",full_url)
                    frappe.db.sql("""
                        UPDATE `tabWorkspace Shortcut`
                        SET url = %s
                        WHERE label = %s
                    """, (full_url, report_name))
                    frappe.db.commit()
            frappe.db.sql("""
                         UPDATE `tabPrepared Report`
                         SET custom_flag = 1
                     """)
            frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"An error occurred: {str(e)}", "Custom Prepared Report Error")
        print(f"An error occurred: {str(e)}")

@frappe.whitelist()
def enqueue_prepared_report():
    control_panel = frappe.get_single("Control Panel")
    report_list = control_panel.prepared_report_list
    if isinstance(report_list, str):
        prepared_report_list = [item.strip() for item in report_list.split(',')]
    else:
        raise ValueError("Report list should be a comma-separated string.")

    if prepared_report_list:
        for report_name in prepared_report_list:
            frappe.call("frappe.desk.query_report.background_enqueue_run",
                        report_name=report_name,
                        filters={})