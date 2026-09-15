import frappe


def run():
	if frappe.db.exists("Client Script", {"dt": "Sales Order", "name": "Job Tracker Strip"}):
		print("CLIENT_SCRIPT_EXISTS")
		return

	with open("/home/frappe/frappe-bench/apps/bot_print_suite/bot_print_suite/client_scripts/job_tracker.js") as f:
		script = f.read()

	frappe.get_doc({
		"doctype": "Client Script",
		"name": "Job Tracker Strip",
		"dt": "Sales Order",
		"view": "Form",
		"enabled": 1,
		"script": script,
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	print("CLIENT_SCRIPT_CREATED")
