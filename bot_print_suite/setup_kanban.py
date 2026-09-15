import frappe


def run():
	if frappe.db.exists("Kanban Board", "Job Board"):
		print("KANBAN_EXISTS")
		return

	frappe.get_doc({
		"doctype": "Kanban Board",
		"kanban_board_name": "Job Board",
		"reference_doctype": "Sales Order",
		"field_name": "custom_job_status",
		"show_labels": 1,
		"columns": [
			{"column_name": "Prepress"}, {"column_name": "Plates"},
			{"column_name": "Printing"}, {"column_name": "Finishing"},
			{"column_name": "QC"}, {"column_name": "Delivered"},
		],
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	print("KANBAN_CREATED")
