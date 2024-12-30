from . import __version__ as app_version

app_name = "third_party_logistics"
app_title = "Third Party Logistics"
app_publisher = "Dexciss Technology Pvt Ltd"
app_description = "3plt"
app_email = "demo@dexciss.com"
app_license = "Dexciss Technology Pvt Ltd"
import frappe

fixtures = [
		{"dt":"Custom Field", "filters": [["name", "in",("Stock Entry-custom_customer_purchase_order",
        "Stock Entry-custom_customer",
        "Customer-custom_is_customer",
        "Customer-custom_is_verified",
        "Customer-custom_send_otp",
        "Item-custom_item_customer",
        "Supplier-custom_is_customer",
        "Supplier-custom_customer"
        ),]]}
]

# from third_party_logistics.third_party_logistics.doctype.client_purchase_order import setup_cron_jobs
# client_purchase_order import setup_cron_jobs
# Includes in <head>
# ------------------
# app_include_js = "/assets/third_party_logistics/public/js/two_step_authentication.js"
# Includes the custom CSS file
# app_include_css = "/assets/third_party_logistics/css/custom_styles.css"
# include js, css files in header of desk.html
# app_include_css = "/assets/third_party_logistics/css/third_party_logistics.css"
# app_include_js = "/assets/third_party_logistics/js/third_party_logistics.js"

# include js, css files in header of web template
# web_include_css = "/assets/third_party_logistics/css/third_party_logistics.css"
# web_include_js = "/assets/third_party_logistics/js/third_party_logistics.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "third_party_logistics/public/scss/website"

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

#####################################################################################3
doctype_js = {"Customer" : ["public/js/two_step_authentication.js" ,"public/js/test.js"],
              "Stock Entry" : "public/js/custom_stock_entry.js",
              "Item":"public/js/custom_item.js",}
############################################################################################
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
#	"methods": "third_party_logistics.utils.jinja_methods",
#	"filters": "third_party_logistics.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "third_party_logistics.install.before_install"
# after_install = "third_party_logistics.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "third_party_logistics.uninstall.before_uninstall"
# after_uninstall = "third_party_logistics.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "third_party_logistics.notifications.get_notification_config"

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
# hooks.py

doc_events = {
    "Pick List": {
        "on_submit": "third_party_logistics.third_party_logistics.doctype.customer_sales_order.customer_sales_order.override_on_submit",
    },
}


# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }
# doc_events = {
#     "Sales Invoice": {
#         "validate": "third_party_logistics.third_party_logistics.custom.override_sales_invoice.override_validate"
#     }
# }
######################################################################
# doc_events = {
#     "Customer": {
#         "on_save": "third_party_logistics.custom_two_step_authentication.send_otp"
#     }
    # "Client Purchase Order" : {
    #     "validate" : "third_party_logistics.third_party_logistics.doctype.client_purchase_order.client_purchase_order.autochange_status"
    # }
# }
#############################################################################

# fixtures = ["Custom Field"]


# Scheduled Tasks
# ---------------
scheduler_events = {
    # "cron": {
    #     "*/5 * * * *": [
    #         "third_party_logistics.third_party_logistics.doctype.client_purchase_order.client_purchase_order.autochange_status"
    #     ]
    # },
    "daily": [
		"third_party_logistics.third_party_logistics.doctype.customer_purchase_order.customer_purchase_order.autochange_status",
        "third_party_logistics.third_party_logistics.doctype.storage_log.storage_log.create_slogs",
        "third_party_logistics.third_party_logistics.doctype.customer_sales_order.customer_sales_order.autochange_status",
	],
}
    # "daily": [
	# 	"third_party_logistics.third_party_logistics.doctype.client_purchase_order.client_purchase_order.daily_scheduled"
	# ],


# scheduler_events = {
#	"all": [
#		"third_party_logistics.tasks.all"
#	],
	# "daily": [
	# 	"third_party_logistics.tasks.daily"
	# ],
#	"hourly": [
#		"third_party_logistics.tasks.hourly"
#	],
#	"weekly": [
#		"third_party_logistics.tasks.weekly"
#	],
#	"monthly": [
#		"third_party_logistics.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "third_party_logistics.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "third_party_logistics.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "third_party_logistics.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["third_party_logistics.utils.before_request"]
# after_request = ["third_party_logistics.utils.after_request"]

# Job Events
# ----------
# before_job = ["third_party_logistics.utils.before_job"]
after_job = ["third_party_logistics.utils.after_job"]

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
# 	"third_party_logistics.auth.validate"
# ]


# doc_events = {
#     "Item": {
# 		"validate": "third_party_logistics.third_party_logistics.custom.custom_item.calculate_volume",
# 	},
# }
