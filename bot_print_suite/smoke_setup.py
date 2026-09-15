import frappe


def run():
	if not frappe.db.exists("Press Profile", "Test Heidelberg SM74"):
		frappe.get_doc({
			"doctype": "Press Profile",
			"press_name": "Test Heidelberg SM74",
			"machine_model": "Heidelberg Speedmaster 74",
			"colour_heads": 4,
			"max_sheet_width_mm": 740,
			"max_sheet_height_mm": 520,
			"gripper_margin_mm": 10,
			"makeready_cost": 500,
			"makeready_sheets": 50,
			"run_waste_pct": 2,
			"running_rate_per_1000": 250,
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("Sheet Size", "700x1000"):
		frappe.get_doc({
			"doctype": "Sheet Size",
			"sheet_size_name": "700x1000",
			"width_mm": 700,
			"height_mm": 1000,
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("Finishing Rate Card", {"operation": "Lamination"}):
		frappe.get_doc({
			"doctype": "Finishing Rate Card",
			"operation": "Lamination",
			"unit_basis": "Per 1000 Sheets",
			"rate": 120,
			"film_foil_type": "Gloss",
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("Customer", "Test Golden Arrow"):
		frappe.get_doc({
			"doctype": "Customer",
			"customer_name": "Test Golden Arrow",
		}).insert(ignore_permissions=True)

	frappe.db.commit()
	print("SETUP_OK")
