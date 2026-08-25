app_name = "unbound_hr"
app_title = "Unbound HR"
app_publisher = "let\'s Unbound"
app_description = "Recruitment automation and ATS for Unbound"
app_email = "himanshu.m@letsunbound.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "unbound_hr",
# 		"logo": "/assets/unbound_hr/logo.png",
# 		"title": "Unbound HR",
# 		"route": "/unbound_hr",
# 		"has_permission": "unbound_hr.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/unbound_hr/css/unbound_hr.css"
# app_include_js = "/assets/unbound_hr/js/unbound_hr.js"

# include js, css files in header of web template
# web_include_css = "/assets/unbound_hr/css/unbound_hr.css"
# web_include_js = "/assets/unbound_hr/js/unbound_hr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "unbound_hr/public/scss/website"

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
# app_include_icons = "unbound_hr/public/icons.svg"

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
# 	"methods": "unbound_hr.utils.jinja_methods",
# 	"filters": "unbound_hr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "unbound_hr.install.before_install"
# after_install = "unbound_hr.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "unbound_hr.uninstall.before_uninstall"
# after_uninstall = "unbound_hr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "unbound_hr.utils.before_app_install"
# after_app_install = "unbound_hr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "unbound_hr.utils.before_app_uninstall"
# after_app_uninstall = "unbound_hr.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "unbound_hr.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "unbound_hr.notifications.get_notification_config"

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

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"unbound_hr.tasks.all"
# 	],
# 	"daily": [
# 		"unbound_hr.tasks.daily"
# 	],
# 	"hourly": [
# 		"unbound_hr.tasks.hourly"
# 	],
# 	"weekly": [
# 		"unbound_hr.tasks.weekly"
# 	],
# 	"monthly": [
# 		"unbound_hr.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "unbound_hr.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "unbound_hr.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "unbound_hr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "unbound_hr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["unbound_hr.utils.before_request"]
# after_request = ["unbound_hr.utils.after_request"]

# Job Events
# ----------
# before_job = ["unbound_hr.utils.before_job"]
# after_job = ["unbound_hr.utils.after_job"]

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
# 	"unbound_hr.auth.validate"
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


after_install = [
    "unbound_hr.setup.ats_fields.create_ats_custom_fields",
]

after_migrate = [
    "unbound_hr.setup.ats_fields.create_ats_custom_fields",
]

app_include_js = [
    "/assets/unbound_hr/js/candidate_detail.js",
]

doc_events = {
    "Job Applicant": {
        "after_insert": "unbound_hr.events.job_applicant.queue_resume_processing",
        "on_update": "unbound_hr.events.job_applicant.queue_resume_processing",
    }
}

website_route_rules = [
    {
        "from_route": "/apply/<path:job_opening>",
        "to_route": "apply",
    }
]
