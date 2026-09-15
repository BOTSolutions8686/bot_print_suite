import frappe


def run():
	if not frappe.db.exists("Custom Field", "Quotation-custom_print_estimate"):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Quotation",
			"fieldname": "custom_print_estimate",
			"label": "Print Estimate",
			"fieldtype": "Link",
			"options": "Print Estimate",
			"insert_after": "order_type",
			"read_only": 1,
		}).insert(ignore_permissions=True)
		print("CUSTOM_FIELD_CREATED")
	else:
		print("CUSTOM_FIELD_EXISTS")
	frappe.db.commit()
