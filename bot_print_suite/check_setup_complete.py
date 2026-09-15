import frappe

def run():
	ss = frappe.get_single("System Settings")
	print("SETUP_COMPLETE:", ss.setup_complete, "LANG:", ss.language, "TZ:", ss.time_zone)
