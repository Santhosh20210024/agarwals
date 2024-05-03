from . import __version__ as app_version

app_name = "agarwals"
app_title = "Agarwals"
app_publisher = "Agarwals"
app_description = "Agarwals"
app_email = "tfs-agarwals@techfinite.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/agarwals/css/agarwals.css"
# app_include_js = "/assets/agarwals/js/agarwals.js"

# include js, css files in header of web template
# web_include_css = "/assets/agarwals/css/agarwals.css"
# web_include_js = "/assets/agarwals/js/agarwals.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "agarwals/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "agarwals.utils.jinja_methods",
#	"filters": "agarwals.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "agarwals.utils.create_folders.folder_structure_creation"
# after_install = "agarwals.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "agarwals.uninstall.before_uninstall"
# after_uninstall = "agarwals.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument


# Agarwals  Integration Setup
before_install = "agarwals.utils.create_folders.folder_structure_creation"

# Agarwals Deletion Setup
# before_uninstall = "agarwals.utils.create_folders.folder_structure_deletion"

# after_app_install = "agarwals.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "agarwals.utils.before_app_uninstall"
# after_app_uninstall = "agarwals.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "agarwals.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    "cron":{
	"*/1 * * * *": [
		"agarwals.settlement_advice_downloader.downloader_job.execute_download_job"
	],
	"5 0 * * *":[
		"agarwals.utils.invoice_update.status_update"
	]
	
	# "daily": [
	# 	"agarwals.tasks.daily"
	# ],
	# "hourly": [
	# 	"agarwals.tasks.hourly"
	# ],
	# "weekly": [
	# 	"agarwals.tasks.weekly"
	# ],
	# "monthly": [
	# 	"agarwals.tasks.monthly"
	# ],
    }
}


# Testing
# -------

# before_tests = "agarwals.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "agarwals.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "agarwals.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["agarwals.utils.before_request"]
# after_request = ["agarwals.utils.after_request"]

# Job Events
# ----------
# before_job = ["agarwals.utils.before_job"]
# after_job = ["agarwals.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"agarwals.auth.validate"
# ]

fixtures = [
    "Custom Field"
]
