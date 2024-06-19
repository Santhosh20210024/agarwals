import frappe

def update_fiscal_year(self,doc,type):
        date = doc.get('date')
        fiscal_year = frappe.get_all('Fiscal Year', filters={'year_start_date':['<=',date],'year_end_date':['>=',date]},fields=['name'])
        yearly_due_doc = frappe.new_doc ('Yearly Due')
        yearly_due_doc.parent = doc.get('name') 
        yearly_due_doc.parenttype = type
        yearly_due_doc.due_amount = 0
        yearly_due_doc.fiscal_year = fiscal_year[0]['name']
        yearly_due_doc.parentfield = 'custom_yearly_due'
        yearly_due_doc.idx = 1
        yearly_due_doc.docstatus = 1
        yearly_due_doc.save()
        frappe.db.commit()
    
    
    
    
    
