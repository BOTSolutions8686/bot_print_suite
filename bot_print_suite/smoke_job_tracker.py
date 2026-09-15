import frappe
from bot_print_suite.production.job_tracker import get_job_tracker_data


def run():
	data = get_job_tracker_data("GA-JOB-2026-0001")
	print("STAGES:", data["stages"])
	print("COMPLETED:", data["completed"])
	print("CURRENT_INDEX:", data["current_index"], "->", data["stages"][data["current_index"]])
	print("STATUS_LINE:", data["status_line"])
