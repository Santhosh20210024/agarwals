import frappe
import re
import unicodedata


class ClaimBookMapper:
    def get_bill_numbers(self):
        query = "SELECT name FROM `tabBill`"
        return frappe.db.sql(query,as_list=True)

    def get_bill_record(self, bill_number):
        return frappe.get_doc('Bill', bill_number)

    def get_claim_records_with_bill_number(self, bill_number, all_claim_records):
        matched_records = []
        for claim_record in all_claim_records:
            if claim_record['custom_raw_bill_number']:
                if bill_number.lower().strip().replace(' ', '') == claim_record[
                    'custom_raw_bill_number'].lower().strip().replace(' ', ''):
                    matched_records.append(claim_record)
        return matched_records

    def match_bill_no_with_final_bill_no(self,bill_record, all_claim_records):
        claim_records = self.get_claim_records_with_bill_number(bill_record.name, all_claim_records)
        if claim_records:
            bill_record.set('no_of_claim_book_record_with_same_bill_number',len(claim_records))
            bill_number_with_final_bill_number = []
            for claim_record in claim_records:
                record = {'claim_book_record_id':claim_record['name'],'al_number':claim_record['al_number'],'cl_number':claim_record['cl_number'],'utr_number':claim_record['utr_number'],'payer':claim_record['tpa_name'],'insurance':claim_record['insurance_company_name']}
                bill_number_with_final_bill_number.append(record)
            bill_record.set('bill_number_with_final_bill_number',bill_number_with_final_bill_number)
            bill_record.save()

    def get_all_claim_records(self):
        query = "SELECT * FROM `tabClaimBook`"
        return frappe.db.sql(query, as_dict = True)

    def format_claim_number(self,claim_id):
        claim_id = unicodedata.normalize("NFKD", claim_id)
        possible_claim_numbers = []
        possible_claim_numbers.append(claim_id)
        possible_claim_id = re.sub(r'-?\((\d)\)$', '', claim_id)
        possible_claim_numbers.append(possible_claim_id)
        formatted_claim_id = claim_id.lower().replace(' ', '').replace('.', '').replace('alnumber', '').replace('number', '').replace(
            'alno', '').replace('al-', '').replace('ccn', '').replace('id:', '').replace('orderid:', '').replace(':',
                                                                                                                 '').replace(
            '(', '').replace(')', '')
        possible_claim_numbers.append(formatted_claim_id)
        possible_claim_id = re.sub(r'-(\d)?$', '', formatted_claim_id)
        possible_claim_numbers.append(possible_claim_id)
        possible_claim_id = re.sub(r'-(\d)?$', r'\1', formatted_claim_id)
        possible_claim_numbers.append(possible_claim_id)
        possible_claim_id = re.sub(r'_(\d)?$', '', formatted_claim_id)
        possible_claim_numbers.append(possible_claim_id)
        possible_claim_id = re.sub(r'_(\d)?$', r'\1', formatted_claim_id)
        possible_claim_numbers.append(possible_claim_id)
        return set(possible_claim_numbers)

    def get_claim_records_with_claim_id(self, key, claim_id_list, all_claim_records):
        matched_records = []
        for claim_record in all_claim_records:
            if claim_record[key]:
                formatted_claim_id = self.format_claim_number(claim_record[key])
                matched_claim_id = claim_id_list.intersection(formatted_claim_id)
                if len(matched_claim_id) > 0:
                    matched_records.append(claim_record)
        return matched_records

    def match_claim_id_with_al_or_cl_number(self,key,bill_record,all_claim_records):
        if bill_record.claim_id:
            claim_id_list = self.format_claim_number(bill_record.claim_id)
            claim_records = self.get_claim_records_with_claim_id(key, claim_id_list, all_claim_records)
            if claim_records:
                bill_record.set('no_of_claim_book_record_with_same_'+key,len(claim_records))
                records = []
                for claim_record in claim_records:
                    record = {'claim_book_record_id':claim_record['name'],'bill_number':claim_record['custom_raw_bill_number'],'utr_number':claim_record['utr_number'],'payer':claim_record['tpa_name'],'insurance':claim_record['insurance_company_name']}
                    records.append(record)
                bill_record.set('claim_id_with_'+key,records)
                bill_record.save()

    def process(self,bill_numbers):
        all_claim_records = self.get_all_claim_records()
        for bill_number in bill_numbers:
            bill_record = self.get_bill_record(bill_number)
            self.match_bill_no_with_final_bill_no(bill_record,all_claim_records)
            self.match_claim_id_with_al_or_cl_number('al_number',bill_record,all_claim_records)
            self.match_claim_id_with_al_or_cl_number('cl_number',bill_record,all_claim_records)
            frappe.db.commit()

    def enqeue_job(self):
        bill_numbers = self.get_bill_numbers()
        print(len(bill_numbers))
        n = 10000
        for i in range(0, len(bill_numbers), n):
            frappe.enqueue(self.process, queue='long', is_async=True, timeout=18000, bill_numbers=bill_numbers[i:i+n])
            print('Job Enqueued')

class FinalDetailsMapper(ClaimBookMapper):

    def get_all_settlement_advice_records(self):
        query = "SELECT * FROM `tabSettlement Advice`"
        return frappe.db.sql(query,as_dict=True)

    def map_final_claim_number(self, bill_record):
        skip = 0
        for record in bill_record.bill_number_with_final_bill_number:
            if bill_record.claim_id:
                if record.al_number and record.al_number == bill_record.claim_id:
                    bill_record.claim_record_id = record.claim_book_record_id
                    bill_record.final_claim_number = record.al_number
                    bill_record.final_payer_name = record.payer
                    bill_record.final_insurance_name = record.insurance
                    bill_record.final_claim_book_utr_number = record.utr_number
                    bill_record.save()
                    frappe.db.commit()
                    skip = 1
                    break

                elif record.cl_number and record.cl_number == bill_record.claim_id:
                    bill_record.claim_record_id = record.claim_book_record_id
                    bill_record.final_claim_number = record.cl_number
                    bill_record.final_payer_name = record.payer
                    bill_record.final_insurance_name = record.insurance
                    bill_record.final_claim_book_utr_number = record.utr_number
                    bill_record.save()
                    frappe.db.commit()
                    skip = 1
                    break
        if skip == 1:
            return

        for record in bill_record.claim_id_with_al_number:
            if record.bill_number and record.bill_number.lower().strip() == bill_record.bill_no.lower().strip():
                bill_record.claim_record_id = record.claim_book_record_id
                bill_record.final_claim_number = bill_record.claim_id
                bill_record.final_payer_name = record.payer
                bill_record.final_insurance_name = record.insurance
                bill_record.final_claim_book_utr_number = record.utr_number
                bill_record.save()
                frappe.db.commit()
                skip = 1
                break

        if skip == 1:
            return

        for record in bill_record.claim_id_with_cl_number:
            if record.bill_number and record.bill_number.lower().strip() == bill_record.bill_no.lower().strip():
                bill_record.claim_record_id = record.claim_book_record_id
                bill_record.final_claim_number = bill_record.claim_id
                bill_record.final_payer_name = record.payer
                bill_record.final_insurance_name = record.insurance
                bill_record.final_claim_book_utr_number = record.utr_number
                bill_record.save()
                frappe.db.commit()
                skip = 1
                break

        if skip == 0:
            bill_record.claim_record_id = "Unable to Find Claim Book Record"
            bill_record.final_claim_number = "Unable to Identify Claim ID"
            bill_record.final_payer_name = "Unable to Identify Payer Name"
            bill_record.final_insurance_name = "Unable to Identify Insurance Name"
            bill_record.final_claim_book_utr_number = "Unable to Identify UTR Number"
            bill_record.save()
            frappe.db.commit()
            return

    def map_settlement_details(self,bill_record,all_settlement_advice_records):
        claim_id_list = self.format_claim_number(bill_record.final_claim_number)
        claim_records = self.get_claim_records_with_claim_id('claim_id',claim_id_list, all_settlement_advice_records)
        if claim_records:
            original_utr_numbers = []
            formated_utr_numbers = []
            settled_amounts = []
            tds_amounts = []
            disallowances = []
            payer_remarks = []
            for record in claim_records:
                original_utr_numbers.append(record['utr_number'])
                formated_utr_numbers.append(record['final_utr_number'])
                settled_amounts.append(str(record['settled_amount']))
                tds_amounts.append(str(record['tds_amount']))
                disallowances.append(str(record['disallowed_amount']))
                payer_remarks.append(str(record['payers_remark']))
            bill_record.final_original_utr_number = ','.join(original_utr_numbers)
            bill_record.final_formatted_utr_number = ','.join(formated_utr_numbers)
            bill_record.settled_amount = ','.join(settled_amounts)
            bill_record.tds_amount = ','.join(tds_amounts)
            bill_record.disallowed_amount = ','.join(disallowances)
            if payer_remarks:
                bill_record.payer_remark = ','.join(payer_remarks)
            bill_record.save()
    def process(self,bill_numbers):
        all_settlement_advice_records = self.get_all_settlement_advice_records()
        for bill_number in bill_numbers:
            bill_record = self.get_bill_record(bill_number)
            self.map_final_claim_number(bill_record)
            if bill_record.final_claim_number == 'Unable to Identify Claim ID':
                continue
            self.map_settlement_details(bill_record,all_settlement_advice_records)
            frappe.db.commit()