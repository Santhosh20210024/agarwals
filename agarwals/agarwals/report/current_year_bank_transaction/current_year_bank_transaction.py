# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

# import frappe
from agarwals.utils.report_data_and_column_getter import get_data_and_columns

def execute(filters=None):
	return get_data_and_columns('Current Year Bank Transaction',filters)