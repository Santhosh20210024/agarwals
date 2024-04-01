from datetime import datetime, timedelta
import frappe

class DSOCalculator:
    def __init__(self):
        self.start_date = datetime.strptime(frappe.get_single('Control Panel').start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(frappe.get_single('Control Panel').end_date, '%Y-%m-%d')

    def get_first_and_last_day_of_month(self,date):
        first_day = datetime(date.year, date.month, 1)
        next_month = first_day.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        return first_day, last_day

    def get_first_and_last_days_between(self):
        result = []
        current_date = self.start_date
        while current_date <= self.end_date:
            first_day, last_day = self.get_first_and_last_day_of_month(current_date)
            result.append({'first_day':first_day.strftime('%Y-%m-%d'), 'last_day':last_day.strftime('%Y-%m-%d')})
            current_date = last_day + timedelta(days=1)
        return result

    def get_revenue_payer_wise(self, first_date, last_date):
        query = f"SELECT customer, sum(total) as current_revenue FROM `tabSales Invoice` WHERE status != 'Cancelled' and posting_date BETWEEN '{first_date}' and '{last_date}' GROUP BY customer"
        total_revenue_payer_wise = frappe.db.sql(query, as_dict=True)
        return total_revenue_payer_wise

    def get_outstanding(self, payer, start_date, end_date):
        outstanding = 0
        sales_invoice_records = frappe.db.sql(
            f"SELECT name, outstanding_amount, rounded_total FROM `tabSales Invoice` WHERE status != 'Cancelled' and posting_date BETWEEN '{start_date}' and '{end_date}' and customer = '{payer}'",
            as_dict=True)
        for record in sales_invoice_records:
            if record['rounded_total'] == record['outstanding_amount']:
                outstanding = outstanding + record['outstanding_amount']
            else:
                settled = frappe.db.sql(
                    f"SELECT SUM(total_allocated_amount) FROM `tabPayment Entry` WHERE custom_sales_invoice = '{record['name']}' and posting_date BETWEEN '{start_date}' and '{end_date}' GROUP BY custom_sales_invoice",
                    as_list=True)
                if not settled:
                    settled = 0
                else:
                    settled = settled[0][0]
                outstanding = outstanding + record['rounded_total'] - settled
        return outstanding

    def create_record(self, payer, last_date, current_revenue, current_outstanding):
        record = frappe.new_doc('Monthwise Revenue and Outstanding')
        record.set('payer', payer)
        record.set('month_last_date', last_date)
        record.set('current_revenue', current_revenue)
        record.set('current_outstanding', current_outstanding)
        record.save()
        frappe.db.commit()
        print("Created")

    def process(self):
        print(self.start_date)
        print(self.end_date)
        first_date_and_last_date = self.get_first_and_last_days_between()
        for record in first_date_and_last_date:
            first_date = record['first_day']
            last_date = record['last_day']
            total_revenue_payer_wise = self.get_revenue_payer_wise(first_date,last_date)
            print(total_revenue_payer_wise)
            for payer_record in total_revenue_payer_wise:
                outstanding = self.get_outstanding(payer_record['customer'], first_date, last_date)
                self.create_record(payer_record['customer'], last_date, payer_record['current_revenue'], outstanding)

@frappe.whitelist()
def initiator():
    DSOCalculator().process()
