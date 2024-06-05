import frappe


class YearlyDueUpdater:
    def __init__(self, previous_fiscal_year, current_fiscal_year,entity):
        self.parent_table = ""
        self.due_field = ""
        self.previous_fiscal_year = previous_fiscal_year
        self.current_fiscal_year = current_fiscal_year
        self.parent_doctype = ""
        self.entity = entity
        self.entity_field = ""
        self.status = ()
    def log_error(self, msg):
        error_log = frappe.new_doc('Error Record Log')
        error_log.set('doctype_name', 'Yearly Due')
        error_log.set('error_message', msg)
        error_log.save()

    def update_previous_year_due(self):
        try:
            query = f"UPDATE `tabYearly Due` tyd JOIN `{self.parent_table}` tp ON tp.name = tyd.parent SET tyd.due_amount = tp.{self.due_field} WHERE tyd.fiscal_year = '{self.previous_fiscal_year}' and tyd.parenttype = '{self.parent_doctype}' and tp.{self.entity_field} = '{self.entity}'"
            frappe.db.sql(query)
            frappe.db.commit()
        except Exception as e:
            self.log_error(e)

    def update_current_fiscal_year(self, records):
        for record in records:
            try:
                doctype = frappe.get_doc(self.parent_doctype, record)
                doc_fiscal_years = frappe.db.sql(f"SELECT fiscal_year FROM `tabYearly Due` WHERE parent = '{record}' AND parenttype = '{self.parent_doctype}'", pluck = 'fiscal_year')
                if self.current_fiscal_year not in doc_fiscal_years:
                    doctype.append('custom_yearly_due',{'fiscal_year':self.current_fiscal_year})
                    doctype.submit()
                    frappe.db.commit()
            except Exception as e:
                self.log_error(e)

    def process(self):
        self.update_previous_year_due()
        records = frappe.db.sql(f"SELECT name FROM `{self.parent_table}` WHERE status NOT IN {self.status} and custom_entity = '{self.entity}'",pluck = 'name')
        for i in range(0, len(records), 100):
            frappe.enqueue(self.update_current_fiscal_year, queue='long', is_async=True, timeout=18000,
                           records=records[i:i + 100])

class SalesInvoiceDueUpdater(YearlyDueUpdater):
    def __init__(self,previous_fiscal_year,current_fiscal_year,entity):
        super().__init__(previous_fiscal_year, current_fiscal_year, entity)
        self.parent_table = "tabSales Invoice"
        self.due_field = 'outstanding_amount'
        self.parent_doctype = "Sales Invoice"
        self.entity_field = "entity"
        self.status = ('Cancelled','Paid')

class BankTransactionDueUpdater(YearlyDueUpdater):
    def __init__(self,previous_fiscal_year, current_fiscal_year,entity):
        super().__init__(previous_fiscal_year, current_fiscal_year, entity)
        self.parent_table = "tabBank Transaction"
        self.due_field = 'unallocated_amount'
        self.parent_doctype = "Bank Transaction"
        self.entity_field = "custom_entity"
        self.status = ('Cancelled', 'Reconciled')

@frappe.whitelist()
def execute():
    previous_fiscal_year = frappe.get_single("Control Panel").closing_fiscal_year
    current_fiscal_year = frappe.get_single("Control Panel").opening_fiscal_year
    entity = frappe.get_single("Control Panel").entity
    BankTransactionDueUpdater(previous_fiscal_year,current_fiscal_year,entity).process()
    SalesInvoiceDueUpdater(previous_fiscal_year,current_fiscal_year,entity).process()