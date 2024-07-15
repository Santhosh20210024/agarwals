import frappe
from agarwals.agarwals.doctype import file_records
from frappe.utils.caching import redis_cache
from frappe import utils
from datetime import date
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from tfs.profiler.timer import Timer


class PaymentEntryCreator:
    """ For Reconcilation Process """

    def add_log_error(self, doctype, record_name=None, error_msg=None):
        error_time = Timer().start(f"add_log_error {doctype} - {record_name}")
        error_log_record = frappe.new_doc('Payment Entry Error Log')
        error_log_record.set('reference_doctype', doctype)
        if record_name:
            error_log_record.set('reference_record', record_name)
        error_log_record.set('error_message', error_msg)
        error_log_record.save()
        error_time.end()

    def update_trans_reference(self, bt_doc, pe_doc):
        update_trans_timer = Timer().start(f"update_trans_reference {bt_doc.name}")
        # bt_doc = frappe.get_doc('Bank Transaction', bt_doc.name)
        bt_doc.append('payment_entries',
                      {'payment_document': 'Payment Entry'
                          , 'payment_entry': pe_doc.name
                          , 'allocated_amount': pe_doc.paid_amount
                          , 'custom_bill_date': pe_doc.custom_due_date
                          , 'custom_bill_region': pe_doc.region
                          , 'custom_bill_branch': pe_doc.branch
                          , 'custom_bill_branch_type': pe_doc.branch_type
                          , 'custom_bill_entity': pe_doc.entity})
        update_trans_submit_timer = Timer().start(f"update_trans_reference_submit {bt_doc.name}")
        bt_doc.submit()
        update_trans_submit_timer.end()
        update_trans_timer.end()

    def process_rounding_off(self, pe_dict, si_doc):
        process_round_timer = Timer().start(f"process_rounding_off")
        deductions = []
        si_outstanding_amount = frappe.get_value('Sales Invoice', si_doc.name, 'outstanding_amount')
        si_allocated_amount = pe_dict["references"][0]["allocated_amount"]
        si_outstanding_amount = round(float(si_outstanding_amount - si_allocated_amount), 2)

        if si_outstanding_amount > 0.00 and si_outstanding_amount <= 9.9:
            deductions.append(
                self.add_deduction('Write Off - A', si_doc, 'WriteOff', round(float(si_outstanding_amount), 2)))

        if deductions:
            pe_dict["references"][0]["allocated_amount"] = round(float(pe_dict["references"][0]["allocated_amount"]),
                                                             2) + round(float(si_outstanding_amount), 2)
            pe_dict["deductions"] = pe_dict["deductions"] + deductions
        process_round_timer.end()
        return pe_dict

    def add_deduction(self, account, si_doc, description, amount):
        return {'account': account, 'cost_center': si_doc.cost_center,
                'description': description, 'branch': si_doc.branch,
                'entity': si_doc.entity, 'region': si_doc.region,
                'branch_type': si_doc.branch_type, 'amount': amount}

    # def create_payment_entry(self, name, si_doc,  bank_account, bt_doc, settled_amount):
    #     create_payment_timer = Timer().start(f"create_payment_entry {si_doc.name}")
    #     pe_doc = frappe.new_doc('Payment Entry')
    #     pe_doc.set('name',name)
    #     pe_doc.set('custom_sales_invoice', si_doc.name)
    #     pe_doc.set('payment_type', 'Receive')
    #     pe_doc.set('mode_of_payment', 'Bank Draft')
    #     pe_doc.set('party_type', 'Customer')
    #     pe_doc.set('party', si_doc.customer)
    #     pe_doc.set('bank_account', bt_doc.bank_account)
    #     pe_doc.set('paid_to', bank_account)
    #     pe_doc.set('paid_from', 'Debtors - A')
    #     pe_doc.set('paid_amount', settled_amount)
    #     pe_doc.set('received_amount', settled_amount)
    #     pe_doc.set('reference_no', bt_doc.reference_number)
    #     pe_doc.set('reference_date', bt_doc.date)
    #     pe_doc.set('cost_center', si_doc.cost_center)
    #     pe_doc.set('branch', si_doc.branch)
    #     pe_doc.set('entity', si_doc.entity)
    #     pe_doc.set('region', si_doc.region)
    #     pe_doc.set('branch_type', si_doc.branch_type)
    #     pe_doc.set('custom_due_date', si_doc.posting_date)
    #     create_payment_timer.end()
    #     return pe_doc

    def create_payment_entry(self, pe_dict):
        create_payment_timer = Timer().start(f"create_payment_entry {pe_dict['name']}")
        pe_doc = frappe.get_doc(pe_dict)
        process_payment_entry_insert_timer = Timer().start(f"process_payment_entry Insert {pe_dict['name']}")
        pe_doc.insert()
        process_payment_entry_insert_timer.end()
        process_payment_entry_submit_timer = Timer().start(f"process_payment_entry Submit {pe_dict['name']}")
        pe_doc.submit()
        process_payment_entry_submit_timer.end()
        create_payment_timer.end()
        return pe_doc

    def get_entry_name(self, si_doc):
        get_entry_name_timer = Timer().start(f"get_entry_name {si_doc.name}")
        existing_payment_entries = frappe.get_list('Payment Entry'
                                                   , filters={'custom_sales_invoice': si_doc.name})

        name = si_doc.name + "-" + str(len(existing_payment_entries)) if existing_payment_entries else si_doc.name
        get_entry_name_timer.end()
        return name

    def get_posting_date(self, bt_doc, si_doc):
        get_posting_timer = Timer().start("get_posting_date")
        closing_date_list = frappe.get_list('Period Closure by Entity',
                                            filters={'entity': si_doc.entity}
                                            , order_by='creation desc'
                                            , pluck='posting_date')

        if closing_date_list:
            closing_date = max(closing_date_list)
            if bt_doc.date < closing_date:
                get_posting_timer.end()
                return utils.today()
            else:
                get_posting_timer.end()
                return bt_doc.date
        else:
            get_posting_timer.end()
            return bt_doc.date

    def process_payment_entry(self
                              , bt_doc
                              , si_doc
                              , bank_account
                              , settled_amount
                              , tds_amount=0
                              , disallowed_amount=0, ref_doc=None):
        process_payment_entry_timer = Timer().start(f"process_payment_entry {si_doc.name}")
        try:
            name = self.get_entry_name(si_doc=si_doc)
            pe_dict = {
                "doctype": "Payment Entry",
                'name': name,
                'custom_sales_invoice': si_doc.name,
                'payment_type': 'Receive',
                'mode_of_payment': 'Bank Draft',
                'party_type': 'Customer',
                'party': si_doc.customer,
                'bank_account': bt_doc.bank_account,
                'paid_to': bank_account,
                'paid_from': 'Debtors - A',
                'paid_amount': settled_amount,
                'received_amount': settled_amount,
                'reference_no': bt_doc.reference_number,
                'reference_date': bt_doc.date,
                'cost_center': si_doc.cost_center,
                'branch': si_doc.branch,
                'entity': si_doc.entity,
                'region': si_doc.region,
                'branch_type': si_doc.branch_type,
                'custom_due_date': si_doc.posting_date,
                'posting_date': self.get_posting_date(bt_doc, si_doc),
                'references': [
                    {
                        'reference_doctype': 'Sales Invoice',
                        'reference_name': si_doc.name,
                        'allocated_amount': settled_amount + tds_amount + disallowed_amount
                    }
                ]
            }
            deductions = []
            if tds_amount > 0:
                deductions.append(self.add_deduction('TDS - A', si_doc, 'TDS', tds_amount))
                pe_dict["custom_tds_amount"] = tds_amount
            if disallowed_amount > 0:
                deductions.append(self.add_deduction('Disallowance - A', si_doc, 'Disallowance', disallowed_amount))
                pe_dict["custom_disallowed_amount"] = disallowed_amount
            if deductions:
                pe_dict["deductions"] = deductions
            pe_dict = self.process_rounding_off(pe_dict, si_doc)
            pe_dict["custom_file_upload"] = ref_doc.file_upload
            pe_dict["custom_transform"] = ref_doc.transform
            pe_dict["custom_index"] = ref_doc.index
            pe_dict["custom_parent_doc"] = ref_doc.name
            pe_doc = self.create_payment_entry(pe_dict)

            self.update_trans_reference(bt_doc, pe_doc)
            file_records.create(file_upload=pe_doc.custom_file_upload,
                                transform=pe_doc.custom_transform, reference_doc=pe_doc.doctype,
                                record=pe_doc.name, index=pe_doc.custom_index)
            process_payment_entry_timer.end()
            return pe_doc
        except Exception as err:
            self.add_log_error('Payment Entry', si_doc.name, error_msg=err)
            process_payment_entry_timer.end()
            return ''

    def get_document_record(self, doctype, name):
        document_timer = Timer().start(f"get_document_record {doctype} - {name}")
        doc = frappe.get_doc(doctype, name)
        document_timer.end()
        return doc

    def update_advice_log(self, advice, status, msg):
        advice_log_timer = Timer().start(f"update_advice_log {advice}")
        frappe.set_value('Settlement Advice', advice, 'status', status)
        frappe.set_value('Settlement Advice', advice, 'remark', msg)
        frappe.db.commit()
        advice_log_timer.end()

    def update_matcher_log(self, name, status, msg):
        macher_log_timer = Timer().start(f"update_matcher_log {name}")
        frappe.set_value('Matcher', name, 'status', status)
        frappe.set_value('Matcher', name, 'remarks', msg)
        frappe.db.commit()
        macher_log_timer.end()

    @redis_cache
    def get_company_account(self, bank_account_name):
        get_company_timer = Timer().start(f"get_company_account {bank_account_name}")
        bank_account = frappe.get_doc('Bank Account', bank_account_name)
        if not bank_account.account:
            get_company_timer.end()
            return None
        get_company_timer.end()
        return bank_account.account

    def update_invoice_reference(self, si_doc, bt_doc, payment_entry, record):
        update_invoice_reference_timer = Timer().start(f"update_invoice_reference {si_doc.name}")
        si_doc.reload()
        # bt_doc = frappe.get_list("Bank Transaction", filters={'name': payment_entry.reference_no}, fields=['bank_account', 'custom_region', 'custom_entity'])
        created_date = date.today().strftime("%Y-%m-%d")

        si_doc.append('custom_reference', {'entry_type': 'Payment Entry', 'entry_name': payment_entry.name,
                                           'paid_amount': payment_entry.paid_amount,
                                           'tds_amount': payment_entry.custom_tds_amount,
                                           'disallowance_amount': payment_entry.custom_disallowed_amount,
                                           'allocated_amount': payment_entry.total_allocated_amount,
                                           'utr_number': payment_entry.reference_no,
                                           'utr_date': payment_entry.reference_date,
                                           'created_date': created_date, 'bank_region': bt_doc.custom_region,
                                           'bank_entity': bt_doc.custom_entity,
                                           'bank_account_number': payment_entry.bank_account})

        if record.settlement_advice:
            si_doc.append('custom_matcher_reference', {'id': record.name, 'match_logic': record.match_logic,
                                                       'settlement_advice': record.settlement_advice})
        else:
            if record.claim_book:
                si_doc.append('custom_matcher_reference',
                              {'id': record.name, 'match_logic': record.match_logic, 'claim_book': record.claim_book})
        frappe.db.set_value('Matcher', record.name, 'status', 'Processed')
        update_invoice_reference_save_timer = Timer().start(f"update_invoice_reference_save {si_doc.name}")
        si_doc.save()
        update_invoice_reference_save_timer.end()
        update_invoice_reference_timer.end()

    def process(self, bt_doc_records, match_logic, chunk_doc):
        """Process: Create payment entry based on the matcher logic ( MA1-CN, MA3-CN, MA5-BN ) only
           param1: bt_doc_records,
           param2: match_logic,
           Return: None
        """
        t1 = Timer().start("Payment Entry Creator Process")
        chunk.update_status(chunk_doc, "InProgress")
        try:
            if not len(bt_doc_records):
                chunk.update_status(chunk_doc, "Processed")
                t1.end()
                return
            count = 1
            for transaction_record in bt_doc_records:
                t2 = Timer().start(f"Loop_{count}_{transaction_record['name']}")
                count += 1
                if not transaction_record['date']:
                    self.add_log_error('Bank Transaction', transaction_record['name'], "Date is Null")
                    t2.end()
                    continue

                bank_account = self.get_company_account(transaction_record['bank_account'])
                if not bank_account:
                    self.add_log_error('Bank Transaction', transaction_record['name'], "No Company Account Found")
                    t2.end()
                    continue

                # Ordered By Payment Order
                # Amount Wise Descending Order
                matcher_records = frappe.db.sql("""
                              SELECT * from `tabMatcher`
                              where match_logic in %(logic)s
                              AND bank_transaction = %(reference_number)s
                              AND status = 'Open' 
                              order by payment_order ASC, tds_amount DESC , disallowance_amount DESC
                              """
                                                , values={'reference_number': transaction_record.name,
                                                          'logic': match_logic}
                                                , as_dict=True)

                if matcher_records:
                    frappe.db.set_value('Bank Transaction', transaction_record['name'], 'custom_advice_status', 'Found')
                ma_count = 1
                for record in matcher_records:
                    t3 = Timer().start(f"Matcher Loop_{ma_count} {record.name}")
                    try:
                        if record.match_logic in ["MA3-CN", "MA3-BN", "MA4-CN", "MA4-BN"]:
                            ref_doc = self.get_document_record('ClaimBook', record.claimbook)
                        else:
                            ref_doc = self.get_document_record('Settlement Advice', record.settlement_advice)
                        bank_amount = 0
                        settled_amount = round(float(record.settled_amount), 2) if record.settled_amount else 0
                        tds_amount = round(float(record.tds_amount), 2) if record.tds_amount else 0
                        disallowance_amount = round(float(record.disallowance_amount),
                                                    2) if record.disallowance_amount else 0

                        if float(settled_amount) < 0 or float(tds_amount) < 0 or float(disallowance_amount) < 0:
                            err_msg = 'Amount Should Not Be Negative'
                            self.update_matcher_log(record.name, 'Error', err_msg)
                            if record.settlement_advice:
                                self.update_advice_log(record.settlement_advice, 'Warning', err_msg)
                            t3.end()
                            continue
                        bt_doc = self.get_document_record('Bank Transaction', record.bank_transaction)
                        unallocated_amount = bt_doc.unallocated_amount
                        if frappe.db.get_value('Bank Transaction', record.bank_transaction,
                                               'status') == 'Reconciled':  # Already Reconciled
                            err_msg = 'Already Reconciled'
                            self.update_matcher_log(record.name, 'Error', err_msg)
                            if record.settlement_advice:
                                self.update_advice_log(record.settlement_advice, 'Warning', err_msg)
                            t3.end()
                            continue

                        if not record.settled_amount:
                            err_msg = 'Settled Amount Should Not Be Zero'
                            self.update_matcher_log(record.name, 'Error', err_msg)
                            if record.settlement_advice:
                                self.update_advice_log(record.settlement_advice, 'Warning', err_msg)
                            t3.end()
                            continue

                        si_doc = self.get_document_record('Sales Invoice', record.sales_invoice)

                        if si_doc.total < (settled_amount + tds_amount + disallowance_amount):
                            err_msg = 'Claim amount lesser than the cumulative of other amounts'
                            self.update_matcher_log(record.name, 'Error', err_msg)
                            if record.settlement_advice:
                                self.update_advice_log(record.settlement_advice, 'Warning', err_msg)
                            t3.end()
                            continue

                        if si_doc.status == 'Paid':
                            err_msg = 'Already Paid Bill'
                            self.update_matcher_log(record.name, 'Error', err_msg)
                            if record.settlement_advice:
                                self.update_advice_log(record.settlement_advice, 'Warning', err_msg)
                            t3.end()
                            continue

                        if si_doc.status == 'Cancelled':
                            err_msg = 'Cancelled Bill'
                            self.update_matcher_log(record.name, 'Error', err_msg)
                            if record.settlement_advice:
                                self.update_advice_log(record.settlement_advice, 'Warning', err_msg)
                            t3.end()
                            continue

                        if record.settlement_advice:
                            settlement_advice = self.get_document_record('Settlement Advice', record.settlement_advice)
                            settlement_advice.set('tpa', si_doc.customer)
                            settlement_advice.set('region', si_doc.region)
                            settlement_advice.set('entity', si_doc.entity)
                            settlement_advice.set('branch_type', si_doc.branch_type)

                        if settled_amount > unallocated_amount:
                            settled_amount = unallocated_amount
                            bank_amount = unallocated_amount

                        # Updating the corresponding fields in settlement advice and claimbook
                        if record.claimbook:
                            if record.settlement_advice:
                                settlement_advice.set('insurance_company_name', record.insurance_company_name)
                                settlement_advice.set('matched_bank_transaction', transaction_record['name'])
                                settlement_advice.set('matched_claimbook_record', record.claimbook)
                                settlement_advice.set('matched_bill_record', record.si_doc)
                            frappe.db.set_value('ClaimBook', record.claimbook, 'matched_status', 'Matched')
                            frappe.db.set_value('Sales Invoice', si_doc.name, 'custom_insurance_name',
                                                record.insurance_company_name)
                        else:
                            if record.settlement_advice:
                                settlement_advice.set('matched_bank_transaction', transaction_record['name'])
                                settlement_advice.set('matched_bill_record', record.si_doc)

                        if si_doc.outstanding_amount < settled_amount:
                            settled_amount = si_doc.outstanding_amount

                        if si_doc.outstanding_amount < settled_amount + tds_amount + disallowance_amount:

                            if si_doc.outstanding_amount >= settled_amount + tds_amount:
                                payment_entry = self.process_payment_entry(
                                    bt_doc
                                    , si_doc
                                    , bank_account
                                    , settled_amount
                                    , tds_amount
                                    , ref_doc=ref_doc)

                                if record.settlement_advice:
                                    settlement_advice.set('remark',
                                                          'Disallowance amount is greater than Outstanding Amount')

                            elif si_doc.outstanding_amount >= settled_amount + disallowance_amount:
                                payment_entry = self.process_payment_entry(
                                    bt_doc
                                    , si_doc
                                    , bank_account
                                    , settled_amount
                                    , disallowance_amount
                                    , ref_doc=ref_doc)

                                if record.settlement_advice:
                                    settlement_advice.set('remark', 'TDS amount is greater than Outstanding Amount')

                            else:
                                payment_entry = self.process_payment_entry(
                                    bt_doc
                                    , si_doc
                                    , bank_account
                                    , settled_amount
                                    , ref_doc=ref_doc)

                                if record.settlement_advice:
                                    settlement_advice.set('remark',
                                                          'Both Disallowed and TDS amount is greater than Outstanding Amount')

                            if payment_entry:
                                self.update_invoice_reference(si_doc, bt_doc, payment_entry, record)
                                if record.settlement_advice:
                                    settlement_advice.set('status', 'Partially Processed')

                            else:
                                if record.settlement_advice:
                                    settlement_advice.set('remark', 'Unable to Create Payment Entry')
                                    settlement_advice.set('status', 'Warning')

                            if record.settlement_advice:
                                settlement_advice.save()

                        else:
                            payment_entry = self.process_payment_entry(
                                bt_doc
                                , si_doc
                                , bank_account
                                , settled_amount
                                , tds_amount
                                , disallowance_amount
                                , ref_doc=ref_doc)

                            if payment_entry:
                                if bank_amount == 0:  # Added due to the validation ( settled_amount = allocated_amount )
                                    if record.settlement_advice:
                                        settlement_advice.set('status', 'Fully Processed')
                                else:
                                    if record.settlement_advice:
                                        settlement_advice.set('status', 'Partially Processed')
                                self.update_invoice_reference(si_doc, bt_doc, payment_entry, record)
                            else:
                                if record.settlement_advice:
                                    settlement_advice.set('remark', 'Unable to Create Payment Entry')
                                    settlement_advice.set('status', 'Warning')
                            if record.settlement_advice:
                                settlement_advice.save()
                        t3.end()
                    except Exception as e:
                        frappe.db.set_value('Matcher', record.name, 'status', 'Error')
                        frappe.db.set_value('Matcher', record.name, 'remarks', e)
                        t3.end()
                    frappe.db.commit()
                t2.end()
            chunk.update_status(chunk_doc, "Processed")
            t1.end()
        except Exception as e:
            log_error(e, 'Matcher')
            chunk.update_status(chunk_doc, "Error")
            t1.end()


def update_reconciled_status():
    update_reconciled_status_timer = Timer().start("update_reconciled_status")
    frappe.db.sql("""update 
                            `tabMatcher` tma
                        join `tabBank Transaction` tbt on
                            tma.bank_transaction = tbt.name
                        JOIN `tabSettlement Advice` tsa on
                            tsa.name = tma.settlement_advice
                        set tma.status = 'Error', tma.remarks = 'Already Reconciled', tsa.status = 'Warning', tsa.remark = 'Already Reconciled'
                        where
                            tbt.status = 'Reconciled'
                            and tma.match_logic in ('MA1-CN', 'MA5-BN')
                            and tma.status = 'Open'""")

    frappe.db.sql("""update `tabMatcher` tma join `tabBank Transaction` tbt on 
                    tma.bank_transaction = tbt.name set tma.status = 'Error',
                    tma.remarks = 'Already Reconciled' where tbt.status = 'Reconciled'
                    and tma.match_logic = 'MA3-CN' and tma.status = 'Open'""")

    frappe.db.commit()
    update_reconciled_status_timer.end()


@frappe.whitelist()
def process(args):
    try:
        process_timer = Timer().start("Payment Intial Process")
        args = cast_to_dic(args)
        seq_no = 0
        chunk_size = int(args["chunk_size"])
        m_logic = tuple(frappe.get_single('Control Panel').match_logic.split(','))
        bt_doc_records = frappe.db.sql("""SELECT name, bank_account, reference_number, date, custom_entity FROM `tabBank Transaction`
                                   WHERE name in ( select bank_transaction from `tabMatcher` where match_logic in %(m_logic)s and status = 'Open' )
                                   AND LENGTH(reference_number) > 4 AND status in ('Pending','Unreconciled') AND deposit > 8 ORDER BY unallocated_amount DESC"""
                                       , values={"m_logic": m_logic}
                                       , as_dict=True)
        update_reconciled_status()
        if bt_doc_records:
            chunk_doc = chunk.create_chunk(args["step_id"])
            PaymentEntryCreator().process(bt_doc_records=bt_doc_records, match_logic=m_logic, chunk_doc=chunk_doc)
            # for record in range(0, len(bt_doc_records), chunk_size):
            #     chunk_doc = chunk.create_chunk(args["step_id"])
            #     seq_no = seq_no + 1
            #     # PaymentEntryCreator().process(bt_doc_records = bt_doc_records, match_logic = m_logic, chunk_doc = chunk_doc)
            #     frappe.enqueue(PaymentEntryCreator().process
            #                    , queue = 'long'
            #                    , is_async = True
            #                    , job_name = "Batch" + str(seq_no)
            #                    , timeout = 25000
            #                    , bt_doc_records = bt_doc_records[record:record + chunk_size]
            #                    , match_logic = m_logic, chunk_doc = chunk_doc)
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
        process_timer.end()
        process_timer.print("payment_process_output_6")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        chunk.update_status(chunk_doc, "Error")
        process_timer.end()
        process_timer.print("payment_process_output_6")
