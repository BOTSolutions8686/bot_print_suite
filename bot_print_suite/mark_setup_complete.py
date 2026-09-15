import frappe

def run():
	ss = frappe.get_single("System Settings")
	if not ss.language:
		ss.language = "en"
	if not ss.time_zone:
		ss.time_zone = "Asia/Riyadh"
	ss.setup_complete = 1
	ss.save(ignore_permissions=True)
	frappe.db.commit()
	print("SETUP_COMPLETE_SET")
