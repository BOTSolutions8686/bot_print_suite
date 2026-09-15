import frappe


def run():
	frappe.db.set_value("User", "Administrator", "language", "ar")
	frappe.db.commit()
	frappe.clear_cache()
	print("Set Administrator language to Arabic")
