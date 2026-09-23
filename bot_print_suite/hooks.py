app_name = "bot_print_suite"
app_title = "BOT Print Suite"
app_publisher = "BOT Solutions"
app_description = "Print estimation and job management for offset printing and packaging"
app_email = "contact@botsolutions.tech"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "bot_print_suite",
# 		"logo": "/assets/bot_print_suite/logo.png",
# 		"title": "BOT Print Suite",
# 		"route": "/bot_print_suite",
# 		"has_permission": "bot_print_suite.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/bot_print_suite/css/bot_print_suite.css"
# app_include_js = "/assets/bot_print_suite/js/bot_print_suite.js"

# include js, css files in header of web template
# web_include_css = "/assets/bot_print_suite/css/bot_print_suite.css"
# web_include_js = "/assets/bot_print_suite/js/bot_print_suite.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "bot_print_suite/public/scss/website"

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

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "bot_print_suite/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "bot_print_suite.utils.jinja_methods",
# 	"filters": "bot_print_suite.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "bot_print_suite.install.before_install"
# after_install = "bot_print_suite.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "bot_print_suite.uninstall.before_uninstall"
# after_uninstall = "bot_print_suite.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "bot_print_suite.utils.before_app_install"
# after_app_install = "bot_print_suite.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "bot_print_suite.utils.before_app_uninstall"
# after_app_uninstall = "bot_print_suite.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "bot_print_suite.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "bot_print_suite.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

doc_events = {
	"Quotation": {
		"before_submit": "bot_print_suite.utils.assign_job_item_to_quotation",
		"on_update": "bot_print_suite.utils.sync_enquiry_status_from_quotation",
	},
	"Work Order": {
		"validate": "bot_print_suite.utils.block_production_without_approved_artwork",
	},
	"Job Card": {
		"on_update": "bot_print_suite.utils.sync_job_status_from_job_card",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"bot_print_suite.tasks.all"
# 	],
# 	"daily": [
# 		"bot_print_suite.tasks.daily"
# 	],
# 	"hourly": [
# 		"bot_print_suite.tasks.hourly"
# 	],
# 	"weekly": [
# 		"bot_print_suite.tasks.weekly"
# 	],
# 	"monthly": [
# 		"bot_print_suite.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "bot_print_suite.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "bot_print_suite.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "bot_print_suite.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "bot_print_suite.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["bot_print_suite.utils.before_request"]
# after_request = ["bot_print_suite.utils.after_request"]

# Job Events
# ----------
# before_job = ["bot_print_suite.utils.before_job"]
# after_job = ["bot_print_suite.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"bot_print_suite.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


# Fixtures
# --------
# All custom fields, workflows, roles etc. that must exist on a fresh
# install ship here (PLAN.md Agent Rules: 'a fresh bench get-app &&
# install-app on a clean site must produce the entire working system with
# zero manual clicks').
fixtures = [
	{"dt": "Cost Driver"},
	{"dt": "Product Estimation Template"},
	{"dt": "Paper Type"},
	{"dt": "Imposition Reference"},
	{"dt": "Translation", "filters": [["language", "=", "ar"]]},
	"Sheet Size",
	"Press Profile",
	{
		"dt": "Custom Field",
		"filters": [
			["dt", "in", ["Quotation", "Sales Order"]],
			["fieldname", "in", ["custom_print_estimate", "custom_job_status"]],
		],
	},
	{"dt": "Workflow State", "filters": [["name", "in", [
		"Draft", "Pending Approval", "Approved", "Rejected",
		"Sent to Customer", "Revision Requested",
	]]]},
	{"dt": "Workflow Action Master", "filters": [["name", "in", [
		"Submit for Approval", "Approve", "Reject", "Revise",
		"Send to Customer", "Request Revision",
	]]]},
	{"dt": "Workflow", "filters": [["name", "in", ["Quotation Approval", "Artwork Approval"]]]},
	{"dt": "Property Setter", "filters": [["doc_type", "=", "Sales Order"], ["field_name", "=", "naming_series"]]},
	{"dt": "Report", "filters": [["name", "=", "Estimated vs Actual"]]},
	{"dt": "Operation", "filters": [["name", "in", ["CTP", "Press", "Lamination", "Foiling", "Embossing", "UV Coating", "Die-cut", "Gluing"]]]},
	{"dt": "Workstation", "filters": [["name", "in", ["CTP", "Laminator", "Die-Cutter", "Gluer"]]]},
	{"dt": "Stock Entry Type", "filters": [["is_standard", "=", 1]]},
	"Manufacturing Settings",
	{"dt": "Number Card", "filters": [["name", "in", ["Open Enquiries", "Estimates Pending", "Quotes Awaiting Approval", "Jobs in Production", "Jobs Due This Week", "Overdue Jobs"]]]},
	{"dt": "Dashboard Chart", "filters": [["name", "in", ["Monthly Sales", "Enquiry Source Breakdown"]]]},
	{"dt": "Kanban Board", "filters": [["name", "=", "Job Board"]]},
	{"dt": "Client Script", "filters": [["name", "=", "Job Tracker Strip"]]},
	{"dt": "Print Format", "filters": [["name", "in", ["Job Ticket", "Print Quotation"]]]},
	{"dt": "Web Form", "filters": [["name", "=", "submit-a-print-enquiry"]]},
	{"dt": "Custom DocPerm", "filters": [["parent", "in", ["Quotation", "Sales Order"]], ["role", "=", "Customer"]]},
	"Portal Settings",
	{"dt": "Workspace Sidebar", "filters": [["name", "=", "Print Suite"]]},
	{"dt": "Desktop Icon", "filters": [["label", "=", "Print Suite"]]},
]
