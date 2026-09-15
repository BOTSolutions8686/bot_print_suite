import frappe
from frappe.model.workflow import apply_workflow
from bot_print_suite.production.start_production import start_production

SO_NAME = "GA-JOB-2026-0002"


def run():
	# 5. Artwork approval
	art = frappe.get_doc({"doctype": "Job Artwork", "sales_order": SO_NAME, "version_no": 1})
	art.insert(ignore_permissions=True)
	art = apply_workflow(art, "Send to Customer")
	art = apply_workflow(art, "Approve")
	print("STEP5_ARTWORK:", art.name, art.status)

	# 6. Start Production
	result = start_production(SO_NAME)
	print("STEP6_PRODUCTION:", result)

	frappe.db.commit()
