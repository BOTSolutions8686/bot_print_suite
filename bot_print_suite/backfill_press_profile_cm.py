import frappe


def run():
	for name in ["Golden Arrow Offset", "Heidelberg SM74"]:
		press = frappe.get_doc("Press Profile", name)
		if not press.max_sheet_width_cm:
			press.max_sheet_width_cm = press.max_sheet_width_mm / 10
			press.max_sheet_height_cm = press.max_sheet_height_mm / 10
			press.save(ignore_permissions=True)
			print(name, "backfilled:", press.max_sheet_width_cm, "x", press.max_sheet_height_cm, "cm")
		else:
			print(name, "already has cm values")
	frappe.db.commit()
