import frappe


def run():
	if frappe.db.exists("Sheet Size", "700x1000") and not frappe.db.exists("Sheet Size", "70x100"):
		frappe.rename_doc("Sheet Size", "700x1000", "70x100", force=True)
		print("Renamed: 700x1000 -> 70x100 (all links auto-updated by Frappe)")
	else:
		print("Already renamed or target exists")
	frappe.db.commit()
