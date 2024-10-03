import frappe


@frappe.whitelist()
def get_data_and_columns(report_name, filters):
    report_configuration = frappe.get_doc("Report Configuration", report_name)
    if filters.get("execute") != 1:
        return [], []
    condition = get_condition(filters, report_configuration)
    if not condition:
        condition = "exists (SELECT 1)"

    query = report_configuration.query.format(condition=condition)
    data = frappe.db.sql(query, as_dict=True)
    columns = eval(report_configuration.columns)
    return columns, data


def get_condition(filters, report_configuration):
    field_and_condition = eval(report_configuration.condition)
    conditions = []
    for filter in filters:
        if filter == 'execute':
            continue
        if filters.get(filter):
            value = filters.get(filter)
            if not isinstance(value, list):
                conditions.append(f"{field_and_condition[filter]} '{value}'")
                continue
            value = tuple(value)
            if len(value) == 1:
                value = "('" + value[0] + "')"
            conditions.append(f"{field_and_condition[filter]} {value}")
    return " and ".join(conditions)
