import frappe


def run():
	if not frappe.db.exists("Custom Field", "Sales Order-custom_job_status"):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Order",
			"fieldname": "custom_job_status",
			"label": "Job Status",
			"fieldtype": "Select",
			"options": "\nPrepress\nPlates\nPrinting\nFinishing\nQC\nDelivered",
			"insert_after": "po_no",
			"read_only": 1,
			"in_list_view": 1,
			"in_standard_filter": 1,
		}).insert(ignore_permissions=True)

	# Add a print-job naming series alongside the stock one, via Property
	# Setter (PLAN.md: "via ERPNext naming series config, not new code").
	existing = frappe.db.get_value("DocField",
		{"parent": "Sales Order", "fieldname": "naming_series"}, "options") or ""
	new_series = "GA-JOB-.YYYY.-.####"
	if new_series not in existing:
		combined = existing.rstrip("\n") + "\n" + new_series
		frappe.make_property_setter({
			"doctype": "Sales Order", "fieldname": "naming_series",
			"property": "options", "value": combined, "property_type": "Text",
		})

	frappe.db.commit()
	print("SALES_ORDER_EXTENDED")
