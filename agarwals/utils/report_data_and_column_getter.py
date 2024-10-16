import frappe

def get_previous_year(fiscal_year):
    query = f"""SELECT
                    name
                FROM
                    `tabFiscal Year`
                WHERE
                    year_end_date = (
                    SELECT
                        (
                        SELECT
                            year_start_date
                        FROM
                            `tabFiscal Year`
                        WHERE
                            name = '{fiscal_year}') - interval 1 day)"""
    return frappe.db.sql(query,pluck='name')[0]

@frappe.whitelist()
def get_data_and_columns(report_name, filters):
    report_configuration = frappe.get_doc("Report Configuration", report_name)
    if filters.get("execute") != 1:
        return [], []
    condition = get_condition(filters, report_configuration)
    if not condition:
        condition = "exists (SELECT 1)"
    query = report_configuration.query
    if report_configuration.fiscal_year_report:
        if filters.get('fiscal_year'):
            fiscal_year = filters.get('fiscal_year')
        else:
            fiscal_year = report_configuration.default_fiscal_year

        fiscal_year_details = frappe.get_doc('Fiscal Year',fiscal_year)
        fy_start_date = fiscal_year_details.year_start_date
        fy_end_date = fiscal_year_details.year_end_date
        previous_year = get_previous_year(fiscal_year)
        query = report_configuration.query.format(fiscal_year = fiscal_year, fy_start_date = fy_start_date, fy_end_date = fy_end_date, previous_year = previous_year, condition = condition)
    else:
        query = query.format(condition=condition)
    data = frappe.db.sql(query, as_dict=True)
    columns = eval(report_configuration.columns)
    return columns, data


def get_condition(filters, report_configuration):
    field_and_condition = eval(report_configuration.condition)
    conditions = []
    for filter in filters:
        if filter == 'execute' or filter == 'fiscal_year':
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