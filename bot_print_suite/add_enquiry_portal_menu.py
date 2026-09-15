import frappe

def run():
	settings = frappe.get_single("Portal Settings")
	existing_routes = [m.route for m in settings.get("custom_menu", [])] + [m.route for m in settings.get("menu", [])]
	if "/print-enquiry" not in existing_routes:
		settings.append("custom_menu", {
			"title": "Print Enquiries",
			"route": "/print-enquiry",
			"reference_doctype": "Print Enquiry",
			"enabled": 1,
		})
		settings.save(ignore_permissions=True)
		print("PORTAL_MENU_ITEM_ADDED")
	else:
		print("ALREADY_EXISTS")
	frappe.db.commit()

