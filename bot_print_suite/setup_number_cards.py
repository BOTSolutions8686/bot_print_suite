import frappe


def _make_number_card(name, label, doctype, filters, function="Count"):
	if frappe.db.exists("Number Card", name):
		return
	frappe.get_doc({
		"doctype": "Number Card",
		"name": name,
		"label": label,
		"document_type": doctype,
		"type": "Document Type",
		"function": function,
		"filters_json": frappe.as_json(filters),
		"is_public": 1,
		"show_percentage_stats": 0,
		"currency": None,
	}).insert(ignore_permissions=True)


def run():
	_make_number_card("Open Enquiries", "Open Enquiries", "Print Enquiry",
		[["Print Enquiry", "status", "=", "New"]])

	_make_number_card("Estimates Pending", "Estimates Pending", "Print Enquiry",
		[["Print Enquiry", "status", "=", "Estimating"]])

	_make_number_card("Quotes Awaiting Approval", "Quotes Awaiting Approval", "Quotation",
		[["Quotation", "workflow_state", "=", "Pending Approval"]])

	_make_number_card("Jobs in Production", "Jobs in Production", "Sales Order",
		[["Sales Order", "docstatus", "=", 1],
		 ["Sales Order", "custom_job_status", "in",
		  ["Prepress", "Plates", "Printing", "Finishing", "QC"]]])

	# These two use a Custom-type card (Python method), not a date-filter
	# card - "Today"/"Today+7" as literal filter values are NOT resolved
	# by plain frappe.get_list (confirmed via smoke test: gave a wrong
	# result via lexical string comparison against date values).
	for name, label, method in [
		("Jobs Due This Week", "Jobs Due This Week", "bot_print_suite.production.job_tracker.count_jobs_due_this_week"),
		("Overdue Jobs", "Overdue Jobs", "bot_print_suite.production.job_tracker.count_overdue_jobs"),
	]:
		if frappe.db.exists("Number Card", name):
			continue
		frappe.get_doc({
			"doctype": "Number Card", "name": name, "label": label,
			"type": "Custom", "method": method, "is_public": 1,
			"currency": None,
			# Custom-type cards route through Frappe's shorten_number(),
			# which has a genuine upstream bug: `if (!number ...) return ""`
			# treats 0 as falsy, rendering blank instead of "0" for any
			# zero-valued Custom card. show_full_number bypasses that path
			# entirely (uses number.toString() directly). Confirmed via
			# browser walkthrough + reading Frappe's own JS source, not
			# assumed - Document Type Count cards don't hit this because
			# they skip shorten_number for the Count function specifically.
			"show_full_number": 1,
		}).insert(ignore_permissions=True)

	frappe.db.commit()
	print("NUMBER_CARDS_CREATED")
