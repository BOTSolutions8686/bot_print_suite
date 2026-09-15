import frappe

def run():
	for app in frappe.get_all("Installed Application", {"app_name": ["in", ["frappe", "erpnext"]]}, ["name", "app_name"]):
		frappe.db.set_value("Installed Application", app.name, "is_setup_complete", 1)
	frappe.db.commit()
	print("DONE:", frappe.get_all("Installed Application", {"app_name": ["in", ["frappe", "erpnext"]]}, ["app_name", "is_setup_complete"]))
