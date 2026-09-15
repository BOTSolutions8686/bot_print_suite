import frappe

def run():
	for doctype in ["Quotation", "Sales Order"]:
		if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": "Customer"}):
			frappe.get_doc({
				"doctype": "Custom DocPerm",
				"parent": doctype,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": "Customer",
				"read": 1,
				"if_owner": 0,
			}).insert(ignore_permissions=True)
			print(f"PERMISSION_ADDED: {doctype} / Customer")
		else:
			print(f"ALREADY_EXISTS: {doctype} / Customer")

	frappe.clear_cache()
	frappe.db.commit()

	# Re-test as the real portal user
	frappe.set_user("abdullatif@goldenarrow-demo.example")
	try:
		result = frappe.get_list("Quotation", fields=["name", "party_name"])
		print("AS_PORTAL_USER_NOW:", result)
	except Exception as e:
		print("STILL_ERROR:", e)
	finally:
		frappe.set_user("Administrator")
