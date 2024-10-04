# Copyright (c) 2024, Agarwals and contributors
# For license information, please see license.txt

import frappe
import pandas as pd
import os
import json
from frappe.model.document import Document
from agarwals.utils.file_util import (
    construct_file_url,SITE_PATH,SHELL_PATH,PROJECT_FOLDER)

class SettlementAdviceConfiguration(Document):
	pass