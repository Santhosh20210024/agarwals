# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt


from frappe.model.document import Document
import frappe
from agarwals.utils.error_handler import log_error
from agarwals.bill_entry.utils import delete_bill_event, update_bill_event

class BillEntryBulk(Document):
	def on_update(self):
		bills = self.bills
		for bill in bills:
			try:
				update_bill_event(bill.bill, self.event, self.date, self.mode_of_submission, self.remarks)
			except Exception as e:
				log_error(error=e,doc="Bill Tracker",doc_name= self.name)

	def on_trash(self):
		for bill in self.bills:
			try:
				delete_bill_event(bill.bill, self.event, self.date, self.mode_of_submission)
			except Exception as e:
				log_error(error=e, doc="Bill Tracker", doc_name=self.name)

def build_html_table(bills_info):
	bills_info_table = """
	<label class="control-label">Bills Information</label>
	<div class="form-grid form-group">
	<div class="grid-heading-row">
	<div class ="grid-row">
	<div class ="data-row row">
	<div class ="col grid-static-col col-xs-1" data-fieldname="s_no" title="S No.">
	<div class ="static-area ellipsis" >S No.</div >
	</div>
	<div class ="col grid-static-col col-xs-1.5" data-fieldname="bill_no" title="Bill No.">
	<div class ="static-area ellipsis" >Bill No.</div >
	</div>
	<div class ="col grid-static-col col-xs-1.5" data-fieldname="bill_date" title="Bill Date">
	<div class ="static-area ellipsis">Bill Date </div>
	</div >
	<div class ="col grid-static-col col-xs-2" data-fieldname="patient_name" title="Patient Name">
	<div class ="static-area ellipsis">Patient Name</div>
	</div >
	<div class ="col grid-static-col col-xs-2" data-fieldname="payer" title="Payer">
	<div class ="static-area ellipsis">Payer</div >
	</div >
	<div class ="col grid-static-col col-xs-2" data-fieldname="claim_id" title="Claim ID">
	<div class ="static-area ellipsis">Claim ID</div>
	</div>
	<div class ="col grid-static-col col-xs-1" data-fieldname="claim_amount" title="Claim Amount" >
	<div class ="static-area ellipsis" >Claim Amount</div>
	</div>
	<div class ="col grid-static-col col-xs-1" data-fieldname="bill_status" title="Bill Status">
	<div class ="static-area ellipsis" >Bill Status</div >
	</div>
	</div>
	</div>
	</div>
	<div class ="grid-body">
	<div class ="rows">
	"""
	count = 0
	for bill in bills_info[::-1]:
		count = count + 1
		bills_info_table +=  f"""
		<div class="grid-row">
        <div class="data-row row">
        <div class="col grid-static-col col-xs-1 " data-fieldname="s_no">
        <div class="static-area ellipsis">{count}</div>
        </div>
        <div class="col grid-static-col col-xs-1.5 " data-fieldname="bill_no">
        <div class="static-area ellipsis">{bill.name}</div>
        </div>
        <div class="col grid-static-col col-xs-1.5" data-fieldname="bill_date">
        <div class="static-area ellipsis">{bill.posting_date}</div>
        </div>
        <div class="col grid-static-col col-xs-2" data-fieldname="patient_name">
    	<div class="static-area ellipsis">{bill.custom_patient_name}</div>
        </div>
        <div class="col grid-static-col col-xs-2" data-fieldname="payer">
        <div class="static-area ellipsis">{bill.customer}</div>
		</div>
        <div class="col grid-static-col col-xs-2" data-fieldname="claim_id">
        <div class="static-area ellipsis">{bill.custom_claim_id}</div>
        </div>
        <div class="col grid-static-col col-xs-1	" data-fieldname="claim_amount">
        <div class="static-area ellipsis">{bill.rounded_total}</div>
        </div>
    	<div class="col grid-static-col col-xs-1" data-fieldname="bill_status">
    	<div class="static-area ellipsis">{bill.status}</div>
        </div>                      
        </div>
        </div>
        """
	return bills_info_table

@frappe.whitelist()
def get_bills_info_table(bills):
	bills = eval(bills)
	bills = tuple(bills)
	if not bills:
		return ""
	if len(bills) == 1:
		bills = '("' + bills[0] + '")'
	query = f"SELECT name, posting_date, custom_patient_name, customer, custom_claim_id, rounded_total, status FROM `tabSales Invoice` WHERE name IN {bills}"
	bills_info = frappe.db.sql(query,as_dict=True)
	return build_html_table(bills_info)