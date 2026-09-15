import frappe


def run():
	ms = frappe.get_single("Manufacturing Settings")
	ms.backflush_raw_materials_based_on = "BOM"
	ms.save(ignore_permissions=True)
	frappe.db.commit()
	print("BACKFLUSH_CONFIGURED:", ms.backflush_raw_materials_based_on)
