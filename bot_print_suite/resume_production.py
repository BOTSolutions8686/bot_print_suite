import frappe
from bot_print_suite.production.start_production import start_production


def run():
	result = start_production("GA-JOB-2026-0001")
	frappe.db.commit()
	print("STEP_6_PRODUCTION_OK:", result)

	so = frappe.get_doc("Sales Order", "GA-JOB-2026-0001")
	print("FINAL_JOB_STATUS:", so.custom_job_status)
