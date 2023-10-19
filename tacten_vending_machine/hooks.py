from . import __version__ as app_version

app_name = "tacten_vending_machine"
app_title = "Tacten Vending Machine"
app_publisher = "Aerele Technologies"
app_description = "Manufactures Vending Machines and deploy it to customer sites"
app_email = "hello@aerele.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tacten_vending_machine/css/tacten_vending_machine.css"
# app_include_js = "/assets/tacten_vending_machine/js/tacten_vending_machine.js"

# include js, css files in header of web template
# web_include_css = "/assets/tacten_vending_machine/css/tacten_vending_machine.css"
# web_include_js = "/assets/tacten_vending_machine/js/tacten_vending_machine.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tacten_vending_machine/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Quotation" : "tacten_vending_machine/client_scripts/quotation.js",
	"Sales Invoice":"tacten_vending_machine/client_scripts/sales_invoice.js",
	"Contract":"tacten_vending_machine/client_scripts/contract.js"
}
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
#	"methods": "tacten_vending_machine.utils.jinja_methods",
#	"filters": "tacten_vending_machine.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tacten_vending_machine.install.before_install"
# after_install = "tacten_vending_machine.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "tacten_vending_machine.uninstall.before_uninstall"
# after_uninstall = "tacten_vending_machine.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "tacten_vending_machine.utils.before_app_install"
# after_app_install = "tacten_vending_machine.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "tacten_vending_machine.utils.before_app_uninstall"
# after_app_uninstall = "tacten_vending_machine.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tacten_vending_machine.notifications.get_notification_config"

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

doc_events = {
	"Contract": {
		"before_save": "tacten_vending_machine.doc_events.contract_before_save",
	},
	"Quotation":{
		"before_save":"tacten_vending_machine.doc_events.qtn_before_save"
	},
	"Purchase Order":{
		"before_save":"tacten_vending_machine.doc_events.po_before_save"
	},
	"Sales Invoice":{
		"before_save":"tacten_vending_machine.doc_events.si_before_save"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily" : [
		"tacten_vending_machine.doc_events.set_carry_fwd_qty_in_pkg"
	]
	# "all": [
	# 	"tacten_vending_machine.tasks.all"
	# ],
	# "daily": [
	# 	"tacten_vending_machine.tasks.daily"
	# ],
	# "hourly": [
	# 	"tacten_vending_machine.tasks.hourly"
	# ],
	# "weekly": [
	# 	"tacten_vending_machine.tasks.weekly"
	# ],
	# "monthly": [
	# 	"tacten_vending_machine.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "tacten_vending_machine.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "tacten_vending_machine.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "tacten_vending_machine.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["tacten_vending_machine.utils.before_request"]
# after_request = ["tacten_vending_machine.utils.after_request"]

# Job Events
# ----------
# before_job = ["tacten_vending_machine.utils.before_job"]
# after_job = ["tacten_vending_machine.utils.after_job"]

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
#	"tacten_vending_machine.auth.validate"
# ]
