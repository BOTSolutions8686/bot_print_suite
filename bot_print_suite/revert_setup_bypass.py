import frappe

def run():
	for app in frappe.get_all("Installed Application", {"app_name": ["in", ["frappe", "erpnext"]]}, ["name"]):
		frappe.db.set_value("Installed Application", app.name, "is_setup_complete", 0)
	ss = frappe.get_single("System Settings")
	ss.setup_complete = 0
	ss.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()
	print("REVERTED")
