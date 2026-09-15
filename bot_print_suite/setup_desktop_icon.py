import frappe

def run():
	if not frappe.db.exists("Desktop Icon", {"label": "Print Suite"}):
		frappe.get_doc({
			"doctype": "Desktop Icon",
			"label": "Print Suite",
			"icon_type": "Link",
			"link_type": "Workspace Sidebar",
			"link_to": "Print Suite",
			"app": "bot_print_suite",
			"icon": "printing",
			"standard": 0,
			"hidden": 0,
		}).insert(ignore_permissions=True)
		print("DESKTOP_ICON_CREATED")
	else:
		print("DESKTOP_ICON_EXISTS")
	frappe.db.commit()
	frappe.clear_cache()
