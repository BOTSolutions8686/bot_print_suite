import frappe
from bot_print_suite.report.estimated_vs_actual.estimated_vs_actual import execute


def run():
	columns, data = execute()
	print("COLUMNS:", [c["fieldname"] for c in columns])
	print("ROW_COUNT:", len(data))
	for row in data:
		print(" ", row)
