import frappe
from agarwals.agarwals.doctype import file_records
from frappe import utils
from datetime import date
from agarwals.reconciliation import chunk
from agarwals.utils.str_to_dict import cast_to_dic
from agarwals.utils.error_handler import log_error
from tfs.profiler.timer import Timer
from agarwals.utils.reconciliation_utils import update_error, get_document_record
from frappe.utils.caching import redis_cache

chunk_status = "Processed"

class BankReconciliation:
    def __validate(self, matcher_record):
        validate_timer = Timer().start(f"Reconciliation validate {matcher_record.name}")
        error = None
        if self.bt_doc.status == 'Reconciled':  # Already Reconciled
            error = 'Already Reconciled'
        elif self.bt_doc.status not in ['Pending', 'Unreconciled']:
            error = 'Status Should be other then Pending, Unreconciled'
        if error:
            update_error(matcher_record, error)
            validate_timer.end()
            return False
        validate_timer.end()
        return True

    def process(self, bt):
        t1 = Timer().start(f"Reconciliation process {bt.bank_transaction}")
        try:
            self.bt_doc = get_document_record("Bank Transaction", bt.bank_transaction)
            matcher_name_list = eval(bt.matcher_names)
            for matcher_name in matcher_name_list:
                t2 = Timer().start(f"Reconciliation Matcher Loop {matcher_name}")
                matcher_doc = get_document_record("Matcher", matcher_name)
                if not self.__validate(matcher_doc):
                    t2.end()
                    continue
                PaymentEntryCreator(matcher_doc, self.bt_doc).process()
                self.bt_doc.reload()
                t2.end()
        except Exception as e:
            global chunk_status
            chunk_status = "Error"
            log_error(e, 'Matcher')
        finally:
            t1.end()

class PaymentEntryCreator:
    def __init__(self, matcher_record, bt_doc):
        class_init_timer = Timer().start(f"Payment_Entry_class_init {matcher_record.name}")
        self.matcher_record = matcher_record
        self.settled_amount = round(float(matcher_record.settled_amount), 2) if matcher_record.settled_amount else 0
        self.tds_amount = round(float(matcher_record.tds_amount), 2) if matcher_record.tds_amount else 0
        self.disallowance_amount = round(float(matcher_record.disallowance_amount), 2) if matcher_record.disallowance_amount else 0
        self.bank_account = self.matcher_record.company_bank_account
        self.sa_status = 'Fully Processed'
        self.sa_remark = ''
        self.pe_doc = None
        self.bt_doc=bt_doc
        class_init_timer.end()

    def __validate(self):
        validate_timer = Timer().start(f"validate {self.matcher_record.name}")
        self.si_doc = get_document_record('Sales Invoice', self.matcher_record.sales_invoice)
        error = None
        if self.si_doc.status == 'Cancelled':
            error = 'Cancelled Bill'
        elif self.si_doc.status== 'Paid':
            error = 'Already Paid Bill'
        elif self.si_doc.total < (self.settled_amount + self.tds_amount + self.disallowance_amount):
            error = 'Claim amount lesser than the cumulative of other amounts'
        if error:
            update_error(self.matcher_record, error)
            validate_timer.end()
            return False
        validate_timer.end()
        return True

    def __set_sa_vars(self, status = 'Partially Processed', remark = ''):
        self.sa_status = status
        self.sa_remark = remark

    def __set_amount(self):
        set_amount_timer = Timer().start(f"set_amount {self.matcher_record.name}")
        unallocated_amount = self.bt_doc.unallocated_amount
        if self.si_doc.outstanding_amount < self.settled_amount + self.tds_amount + self.disallowance_amount and self.si_doc.outstanding_amount >= self.settled_amount + self.tds_amount:
            self.disallowance_amount = 0
            self.__set_sa_vars(remark='Disallowance amount is greater than Outstanding Amount')
        elif self.si_doc.outstanding_amount < self.settled_amount + self.tds_amount + self.disallowance_amount and self.si_doc.outstanding_amount >= self.settled_amount + self.disallowance_amount:
            self.tds_amount = 0
            self.__set_sa_vars(remark='TDS amount is greater than Outstanding Amount')
        elif self.si_doc.outstanding_amount < self.settled_amount + self.tds_amount + self.disallowance_amount:
            self.tds_amount = 0
            self.disallowance_amount = 0
            self.__set_sa_vars(remark='Both Disallowed and TDS amount is greater than Outstanding Amount')
        if self.settled_amount > unallocated_amount:
            self.settled_amount = unallocated_amount
            self.__set_sa_vars(remark="Bank Transcation unalllocated is less than settled amount")
        if self.si_doc.outstanding_amount < self.settled_amount:
            self.settled_amount = self.si_doc.outstanding_amount
            self.__set_sa_vars(remark="Sales Invoice Outstanding is less than settled amount")
        set_amount_timer.end()

    def __get_entry_name(self):
        get_entry_name_timer = Timer().start(f"get_entry_name {self.si_doc.name}")
        existing_payment_entries = frappe.get_list('Payment Entry'
                                                   , filters={'custom_sales_invoice': self.si_doc.name})
        name = self.si_doc.name + "-" + str(len(existing_payment_entries)) if existing_payment_entries else self.si_doc.name
        get_entry_name_timer.end()
        return name

    @staticmethod
    @redis_cache
    def get_entity_closing_date(entity):
        get_posting_date_timer = Timer().start(f"get_posting_date {entity}")
        closing_date_list = frappe.get_list('Period Closure by Entity',
                                            filters={'entity': entity}
                                            , order_by='creation desc'
                                            , pluck='posting_date')
        closing_date = max(closing_date_list) if closing_date_list else None
        get_posting_date_timer.end()
        return closing_date

    def __get_posting_date(self):
        get_posting_date_timer = Timer().start(f"get_posting_date {self.matcher_record.name}")
        closing_date = self.get_entity_closing_date(self.matcher_record.si_entity)
        if closing_date and self.bt_doc.date < closing_date:
            get_posting_date_timer.end()
            return utils.today()
        get_posting_date_timer.end()
        return self.bt_doc.date

    def __add_deduction(self, account, description, amount):
        return {'account': account, 'cost_center': self.si_doc.cost_center,
                'description': description, 'branch': self.si_doc.branch,
                'entity': self.si_doc.entity, 'region': self.si_doc.region,
                'branch_type': self.si_doc.branch_type, 'amount': amount}

    def __process_write_off(self, pe_dict):
        process_round_timer = Timer().start(f"process_write_off {pe_dict['name']} ")
        deductions = []
        si_outstanding_amount = self.si_doc.outstanding_amount
        si_allocated_amount = pe_dict["references"][0]["allocated_amount"]
        si_outstanding_amount = round(float(si_outstanding_amount - si_allocated_amount), 2)
        if si_outstanding_amount > 0.00 and si_outstanding_amount <= 9.9:
            deductions.append(
                self.__add_deduction('Write Off - A','WriteOff', round(float(si_outstanding_amount), 2)))
        if deductions:
            pe_dict["references"][0]["allocated_amount"] = round(float(pe_dict["references"][0]["allocated_amount"]),
                                                             2) + round(float(si_outstanding_amount), 2)
            pe_dict["deductions"] = pe_dict["deductions"] + deductions
        process_round_timer.end()
        return pe_dict

    def __create_payment_entry(self, pe_dict):
        create_payment_timer = Timer().start(f"create_payment_entry {pe_dict['name']}")
        pe_doc = frappe.get_doc(pe_dict)
        process_payment_entry_insert_timer = Timer().start(f"payment_entry Insert {pe_dict['name']}")
        pe_doc.insert()
        process_payment_entry_insert_timer.end()
        process_payment_entry_submit_timer = Timer().start(f"payment_entry_Submit {pe_dict['name']}")
        pe_doc.submit()
        process_payment_entry_submit_timer.end()
        create_payment_timer.end()
        return pe_doc

    def __process_payment_entry(self):
        process_payment_entry_timer = Timer().start(f"process_payment_entry {self.si_doc.name}")
        try:
            name = self.__get_entry_name()
            pe_dict = {
                "doctype": "Payment Entry",
                'name': name,
                'custom_sales_invoice': self.si_doc.name,
                'payment_type': 'Receive',
                'mode_of_payment': 'Bank Draft',
                'party_type': 'Customer',
                'party': self.si_doc.customer,
                'bank_account': self.bt_doc.bank_account,
                'paid_to': self.bank_account,
                'paid_from': 'Debtors - A',
                'paid_amount': self.settled_amount,
                'received_amount': self.settled_amount,
                'reference_no': self.bt_doc.reference_number,
                'reference_date': self.bt_doc.date,
                'cost_center': self.si_doc.cost_center,
                'branch': self.si_doc.branch,
                'entity': self.si_doc.entity,
                'region': self.si_doc.region,
                'branch_type': self.si_doc.branch_type,
                'custom_due_date': self.si_doc.posting_date,
                'posting_date': self.__get_posting_date(),
                'references': [
                    {
                        'reference_doctype': 'Sales Invoice',
                        'reference_name': self.si_doc.name,
                        'allocated_amount': self.settled_amount + self.tds_amount + self.disallowance_amount
                    }
                ]
            }
            deductions = []
            if self.tds_amount > 0:
                deductions.append(self.__add_deduction('TDS - A', 'TDS', self.tds_amount))
                pe_dict["custom_tds_amount"] = self.tds_amount
            if self.disallowance_amount > 0:
                deductions.append(self.__add_deduction('Disallowance - A', 'Disallowance', self.disallowance_amount))
                pe_dict["custom_disallowed_amount"] = self.disallowance_amount
            if deductions:
                pe_dict["deductions"] = deductions
            pe_dict = self.__process_write_off(pe_dict)
            pe_dict["custom_file_upload"] = self.matcher_record.file_upload
            pe_dict["custom_transform"] = self.matcher_record.transform
            pe_dict["custom_index"] = self.matcher_record.index
            if self.matcher_record.settlement_advice:
                pe_dict["custom_parent_doc"] = self.matcher_record.settlement_advice
            else:
                pe_dict["custom_parent_doc"] = self.matcher_record.claimbook
            pe_doc = self.__create_payment_entry(pe_dict)
            file_records.create(file_upload=pe_doc.custom_file_upload,
                                transform=pe_doc.custom_transform, reference_doc=pe_doc.doctype,
                                record=pe_doc.name, index=pe_doc.custom_index)
            self.pe_doc = pe_doc
            process_payment_entry_timer.end()
        except Exception as e:
            self.__set_sa_vars("Warning", 'Unable to Create Payment Entry')
            process_payment_entry_timer.end()
            raise Exception(e)
    #
    # def __update_invoice_reference(self):
    #     update_invoice_reference_timer = Timer().start(f"update_invoice_reference {self.si_doc.name}")
    #     self.si_doc.reload()
    #     created_date = date.today().strftime("%Y-%m-%d")
    #     self.si_doc.append('custom_reference', {'entry_type': 'Payment Entry', 'entry_name': self.pe_doc.name,
    #                                        'paid_amount': self.pe_doc.paid_amount,
    #                                        'tds_amount': self.pe_doc.custom_tds_amount,
    #                                        'disallowance_amount': self.pe_doc.custom_disallowed_amount,
    #                                        'allocated_amount': self.pe_doc.total_allocated_amount,
    #                                        'utr_number': self.pe_doc.reference_no,
    #                                        'utr_date': self.pe_doc.reference_date,
    #                                        'created_date': created_date, 'bank_region': self.bt_doc.custom_region,
    #                                        'bank_entity': self.bt_doc.custom_entity,
    #                                        'bank_account_number': self.pe_doc.bank_account})
    #     if self.matcher_record.settlement_advice:
    #         ref_key, ref_value = 'settlement_advice', self.matcher_record.settlement_advice
    #     else:
    #         ref_key, ref_value = 'claim_book', self.matcher_record.claim_book
    #         self.si_doc.custom_insurance_name = self.matcher_record.insurance_company_name
    #     self.si_doc.append('custom_matcher_reference',
    #                           {'id': self.matcher_record.name, 'match_logic': self.matcher_record.match_logic, ref_key: ref_value})
    #     update_invoice_reference_save_timer = Timer().start(f"update_invoice_reference_save {self.si_doc.name}")
    #     self.si_doc.save()
    #     update_invoice_reference_save_timer.end()
    #     update_invoice_reference_timer.end()

    def __update_trans_reference(self):
        update_trans_timer = Timer().start(f"update_trans_reference {self.bt_doc.name}")
        self.bt_doc.append('payment_entries',
                      {'payment_document': 'Payment Entry'
                          , 'payment_entry': self.pe_doc.name
                          , 'allocated_amount': self.pe_doc.paid_amount
                          , 'custom_bill_date': self.pe_doc.custom_due_date
                          , 'custom_bill_region': self.pe_doc.region
                          , 'custom_bill_branch': self.pe_doc.branch
                          , 'custom_bill_branch_type': self.pe_doc.branch_type
                          , 'custom_bill_entity': self.pe_doc.entity})
        self.bt_doc.custom_advice_status = 'Found'
        update_trans_submit_timer = Timer().start(f"update_trans_reference_submit {self.bt_doc.name}")
        self.bt_doc.submit()
        update_trans_submit_timer.end()
        update_trans_timer.end()

    def __update_advice_reference(self):
        update_advice_reference_timer = Timer().start(f"update_advice_reference {self.matcher_record.name}")
        if not self.matcher_record.settlement_advice:
            return None
        settlement_advice = get_document_record('Settlement Advice', self.matcher_record.settlement_advice)
        sa_dict = {'tpa': self.si_doc.customer,
                    'region': self.si_doc.region,
                    'entity': self.si_doc.entity,
                    'branch_type': self.si_doc.branch_type,
                    'matched_bank_transaction': self.bt_doc.name,
                    'matched_bill_record': self.si_doc.name,
                    'status': self.sa_status,
                    'remark': self.sa_remark
        }
        if self.matcher_record.claimbook:
            sa_dict['matched_claimbook_record'], sa_dict['insurance_company_name'] = self.matcher_record.claimbook, self.matcher_record.insurance_company_name
        settlement_advice.update(sa_dict)
        settlement_advice.save()
        update_advice_reference_timer.end()

    def __update_claim_reference(self):
        update_claim_referece = Timer().start(f"update_claim_reference {self.matcher_record.name}")
        frappe.db.sql(
            f"""UPDATE `tabClaimBook` SET matched_status = 'Matched' WHERE name = \"{self.matcher_record.claimbook}\"""")
        update_claim_referece.end()

    def __update_references(self):
        update_reference_timer = Timer().start(f"update_reference {self.matcher_record.name}")
        # self.__update_invoice_reference()
        self.__update_trans_reference()
        self.__update_advice_reference()
        self.__update_claim_reference()
        update_reference_timer.end()

    def process(self):
        Payment_creation_process_timer = Timer().start(f"Payment_creation_process {self.matcher_record.name}")
        try:
            if not self.__validate():
                return
            self.__set_amount()
            self.__process_payment_entry()
            self.__update_references()
            self.matcher_record.status = 'Processed'
        except Exception as e:
            frappe.db.rollback()
            update_error(self.matcher_record, self.sa_remark, e)
            global chunk_status
            chunk_status = "Error"
        finally:
            self.matcher_record.save()
            frappe.db.commit()
            Payment_creation_process_timer.end()

def reconcile_bank_transaction(bt_records, chunk_doc, batch):
    t1 = Timer().start(f"reconcile_bank_transaction {batch}")
    chunk.update_status(chunk_doc, "InProgress")
    try:
        for bt in bt_records:
            t2 = Timer().start(f"BankReconciliation {bt.bank_transaction}")
            BankReconciliation().process(bt)
            t2.end()
    except Exception as e:
        global chunk_status
        chunk_status = "Error"
        log_error(e, 'Matcher')
    finally:
        chunk.update_status(chunk_doc, chunk_status)
        t1.end()
        t1.print(batch)

@frappe.whitelist()
def process(args):
    try:
        args = cast_to_dic(args)
        seq_no = 0
        chunk_size = int(args["chunk_size"])
        m_logic = tuple(frappe.get_single('Control Panel').match_logic.split(','))
        bt_records = frappe.db.sql("""SELECT bank_transaction, JSON_ARRAYAGG(name) as matcher_names
                                        FROM `tabMatcher`
                                        where match_logic in  %(m_logic)s and status = 'Open'
                                        GROUP BY bank_transaction ORDER BY sales_invoice,unallocated DESC;"""
                                       ,values={"m_logic": m_logic}
                                       ,as_dict=True)
        if bt_records:
            for record in range(0, len(bt_records), chunk_size):
                chunk_doc = chunk.create_chunk(args["step_id"])
                seq_no = seq_no + 1
                # reconcile_bank_transaction(bt_records=bt_records, chunk_doc=chunk_doc, batch = "Batch" + str(seq_no))
                frappe.enqueue(reconcile_bank_transaction
                               , queue = 'long'
                               , is_async = True
                               , job_name = "Batch" + str(seq_no)
                               , timeout = 25000
                               , bt_records = bt_records[record:record + chunk_size]
                               , chunk_doc = chunk_doc, batch = "Batch" + str(seq_no))
        else:
            chunk_doc = chunk.create_chunk(args["step_id"])
            chunk.update_status(chunk_doc, "Processed")
    except Exception as e:
        chunk_doc = chunk.create_chunk(args["step_id"])
        log_error(e, "Matcher")
        chunk.update_status(chunk_doc, "Error")