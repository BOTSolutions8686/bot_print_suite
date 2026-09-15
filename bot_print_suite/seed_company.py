import frappe


def run():
	if not frappe.db.exists("Company", "Golden Arrow Printing"):
		frappe.get_doc({
			"doctype": "Company",
			"company_name": "Golden Arrow Printing",
			"abbr": "GAP",
			"default_currency": "SAR",
			"country": "Saudi Arabia",
		}).insert(ignore_permissions=True)

	frappe.db.set_default("company", "Golden Arrow Printing")
	frappe.db.commit()
	print("COMPANY_SEEDED")
