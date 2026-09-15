import frappe

USER = "abdullatif@goldenarrow-demo.example"
CUSTOMER = "Golden Arrow Printing & Packaging Co."

def run():
	if not frappe.db.exists("User Permission", {"user": USER, "allow": "Customer", "for_value": CUSTOMER}):
		frappe.get_doc({
			"doctype": "User Permission",
			"user": USER,
			"allow": "Customer",
			"for_value": CUSTOMER,
			"apply_to_all_doctypes": 1,
		}).insert(ignore_permissions=True)
		print("USER_PERMISSION_CREATED")
	else:
		print("USER_PERMISSION_EXISTS")
	frappe.db.commit()
