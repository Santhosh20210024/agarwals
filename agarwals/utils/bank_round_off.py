import frappe
def create_journal_entry(ype, date):
    je = frappe.new_doc('Journal Entry')
    je.voucher_type = ype
    je.posting_date = date
    return je

def fetch_bank_details(bank):
    return frappe.get_doc('Bank Transaction', bank)

def add_account_entries(je, bank,  to_account, amount):
    print(bank.bank_account)
    account = frappe.get_doc('Bank Account',bank.bank_account)
    print(account.account)
    from_account = account.account
    je.append('accounts', {
        'account': from_account,
        'party_type': 'Customer',
        'party': bank.party,
        'credit_in_account_currency': amount,
        'reference_type': 'Bank Transaction',
        'reference_name': bank.name,
        'reference_due_date': bank.date
    })
    je.append('accounts', {
        'account': to_account,
        'party_type': 'Customer',
        'party': bank.party,
        'debit_in_account_currency': amount,
        'user_remark': to_account
    })
    return je

def save_je(je, parent_doc=None):
    if parent_doc:
        je.custom_file_upload = parent_doc.transform
        je.custom_transform = parent_doc.transform
        je.custom_index = parent_doc.index
    print(je)
    je.save()
    je.submit()
    frappe.db.commit()
    # if parent_doc:
    #     file_records.create(file_upload=je.custom_file_upload, transform=je.custom_transform, reference_doc=je.doctype,
    #                         record=je.name, index=je.custom_index)

def process_round_off(rnd_unallocated):
    for bank in rnd_unallocated:
        bank_ = fetch_bank_details(bank)
        try:
            je = create_journal_entry('Credit Note', bank_.date)
            je.name = "".join([bank_.name, '-', 'RND'])
            je = add_account_entries(je, bank_, 'Rounded Off - A', bank_.unallocated_amount)
            save_je(je)
            update_trans_reference(bank, je)
        except Exception as e:
            print(str(e))

def get_round_off_bills():
    bank = frappe.qb.DocType('Bank Transaction')
    bank_query = (
        frappe.qb.from_(bank)
        .select(bank.name, bank.date, bank.unallocated_amount)
        .where((bank.unallocated_amount <= 9.9))
        .where((bank.status == 'Unreconciled'))
    )
    return frappe.db.sql(bank_query, as_dict=True)
def update_trans_reference(bt_doc, pe_doc):
        bt_doc = frappe.get_doc('Bank Transaction', bt_doc.name)
        bt_doc.append('payment_entries',
                      {'payment_document': 'Journal Entry'
                      ,'payment_entry':pe_doc.name
                       ,'allocated_amount':pe_doc.total_credit
                      ,'custom_posting_date':pe_doc.posting_date
                      ,'custom_creation_date':pe_doc.creation})
        bt_doc.submit()
        frappe.db.commit()
        
@frappe.whitelist()        
def process():
	rnd_unallocated = get_round_off_bills()
	process_round_off(rnd_unallocated)