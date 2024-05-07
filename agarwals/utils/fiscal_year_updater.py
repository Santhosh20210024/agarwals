import frappe
import datetime

def update_year_in_invoice(invoice, year):
    fiscal_years = []
    print(year)
    for i in year:
        fiscal_years.append({'year':i})
    try:
        sales_invoice = frappe.get_doc('Sales Invoice', invoice)
        sales_invoice.set('custom_fiscal_year', fiscal_years)
        sales_invoice.submit()
        frappe.db.commit()
    except Exception as e:
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('error_message', e)
        error_log.save()
@frappe.whitelist()
def update_year():
    sales_invoices = frappe.get_all('Sales Invoice', filters={'status': ['!=', 'Cancelled']},
                                    fields=['name', 'posting_date'])
    for i in range(0, len(sales_invoices), 1000):
        frappe.enqueue(update_fiscal_year, queue='long', is_async=True, timeout=18000,
                       sales_invoices=sales_invoices[i:i + 1000])
        print('Enqueued')

def update_fiscal_year(sales_invoices):
    for invoice in sales_invoices:
        year = []
        if invoice['posting_date'].month < 4 and invoice['posting_date'].year == 2019:
            year = ['2018','2019','2020','2021','2022','2023']
        elif invoice['posting_date'].month >= 4 and invoice['posting_date'].year == 2019:
            year = ['2019', '2020', '2021', '2022', '2023']
        elif invoice['posting_date'].month < 4 and invoice['posting_date'].year == 2020:
            year = ['2019', '2020', '2021', '2022', '2023']
        elif invoice['posting_date'].month >= 4 and invoice['posting_date'].year == 2020:
            year = ['2020', '2021', '2022', '2023']
        elif invoice['posting_date'].month < 4 and invoice['posting_date'].year == 2021:
            year = ['2020', '2021', '2022', '2023']
        elif invoice['posting_date'].month >= 4 and invoice['posting_date'].year == 2021:
            year = ['2021', '2022', '2023']
        elif invoice['posting_date'].month < 4 and invoice['posting_date'].year == 2022:
            year = ['2021', '2022', '2023']
        elif invoice['posting_date'].month >= 4 and invoice['posting_date'].year == 2022:
            year = ['2022', '2023']
        elif invoice['posting_date'].month < 4 and invoice['posting_date'].year == 2023:
            year = ['2022', '2023']
        elif invoice['posting_date'].month >= 4 and invoice['posting_date'].year == 2023:
            year = ['2023']
        elif invoice['posting_date'].month < 4 and invoice['posting_date'].year == 2024:
            year = ['2023']
        update_year_in_invoice(invoice,year)