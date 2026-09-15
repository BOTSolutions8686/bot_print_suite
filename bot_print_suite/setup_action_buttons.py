import frappe
import os

BASE = os.path.dirname(os.path.abspath(__file__)) + "/client_scripts"

SCRIPTS = [
	("Print Enquiry Actions", "Print Enquiry", f"{BASE}/print_enquiry.js"),
	("Print Estimate Actions", "Print Estimate", f"{BASE}/print_estimate.js"),
	("Job Order Actions", "Sales Order", f"{BASE}/job_order_actions.js"),
]


def run():
	for name, dt, path in SCRIPTS:
		script_text = open(path).read()
		if frappe.db.exists("Client Script", name):
			doc = frappe.get_doc("Client Script", name)
			doc.script = script_text
			doc.save(ignore_permissions=True)
			print(f"UPDATED: {name}")
		else:
			frappe.get_doc({
				"doctype": "Client Script",
				"name": name,
				"dt": dt,
				"view": "Form",
				"enabled": 1,
				"script": script_text,
			}).insert(ignore_permissions=True)
			print(f"CREATED: {name}")
	frappe.db.commit()
