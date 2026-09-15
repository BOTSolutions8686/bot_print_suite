import frappe


def run():
	frappe.db.set_value("User", "Administrator", "language", None)
	frappe.db.commit()
	frappe.clear_cache()
	print("Reverted Administrator language to default")
