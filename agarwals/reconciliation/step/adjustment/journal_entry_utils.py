import frappe
from agarwals.agarwals.doctype import file_records


class JournalEntryUtils:
    """This Utils is only for creating journal entry against the sales invoice and bank transaction"""
    def __init__(self, doctype):
        self.doctype = doctype
        self.party_type = 'Customer'

    def create_journal_entry(self, type, date):
        je = frappe.new_doc("Journal Entry")
        je.voucher_type = type
        je.posting_date = date
        return je

    def set_je_name(self, *args):
        return "".join(args)

    def fetch_doc_details(self, doctype, doc_id):
        try:
            return frappe.get_doc(doctype, doc_id)
        except frappe.DoesNotExistError:
            frappe.throw(f"{doctype} {doc_id} not found.")

    def add_account_entries(self, je, doc, from_account, to_account, amount):
        self._add_account_entry(
            je, from_account, doc, amount, credit=True
        )
        self._add_account_entry(
            je, to_account, doc, amount, credit=False
        )
        return je
    
    def _add_account_entry(self, je, account, doc, amount, credit):
        entry = {
                "account": account,
                "party_type": self.party_type,
                "party": doc.get('customer', doc.get('party')),
                "reference_type": self.doctype,
                "reference_name": doc.name,
                "reference_due_date": doc.get('posting_date', doc.get('date')),
                "region": doc.get('region', doc.get('custom_region','')),
                "entity": doc.get('entity', doc.get('custom_region','')),
                "branch": doc.get('branch', doc.get('custom_branch', '')),
                "cost_center": doc.get('cost_center', ''),
                "branch_type": doc.get('custom_branch_type', doc.get('branch_type', ''))
            }

        if credit:
            entry["credit_in_account_currency"] = amount
        else:
            entry["debit_in_account_currency"] = amount
            entry["user_remark"] = account

        je.append("accounts", entry)
    
    def save_je(self, je, parent_doc=None):
        self._set_custom_fields(je, parent_doc)
        je.save()
        je.submit()
        frappe.db.commit()
        self._create_file_record(je, parent_doc)

    def _set_custom_fields(self, je, parent_doc):
        if parent_doc:
            je.custom_file_upload = parent_doc.transform
            je.custom_transform = parent_doc.transform
            je.custom_index = parent_doc.index

    def _create_file_record(self, je, parent_doc):
        if parent_doc:
            file_records.create(
                file_upload=je.custom_file_upload,
                transform=je.custom_transform,
                reference_doc=je.doctype,
                record=je.name,
                index=je.custom_index,
            )
