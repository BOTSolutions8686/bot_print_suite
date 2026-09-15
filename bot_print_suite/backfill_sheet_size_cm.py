import frappe


def run():
	# Backfill cm values on the existing record from its already-correct
	# mm values - critical BEFORE this record is ever saved again, since
	# width_mm/height_mm are now computed FROM width_cm/height_cm, and an
	# unset width_cm would zero out the correct 700/1000 on next save.
	sheet = frappe.get_doc("Sheet Size", "700x1000")
	if not sheet.width_cm:
		sheet.width_cm = sheet.width_mm / 10
		sheet.height_cm = sheet.height_mm / 10
		sheet.save(ignore_permissions=True)
		print("Backfilled:", sheet.width_cm, "x", sheet.height_cm, "cm")
	else:
		print("Already has cm values:", sheet.width_cm, sheet.height_cm)
	frappe.db.commit()
