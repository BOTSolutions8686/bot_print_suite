import frappe

CUSTOMER = "Golden Arrow Printing & Packaging Co."
PORTAL_EMAIL = "abdullatif@goldenarrow-demo.example"

def run():
	customer = frappe.get_doc("Customer", CUSTOMER)
	existing = [pu.user for pu in customer.get("portal_users", [])]
	if PORTAL_EMAIL not in existing:
		customer.append("portal_users", {"user": PORTAL_EMAIL})
		customer.save(ignore_permissions=True)
		frappe.db.commit()
		print("ADDED_TO_PORTAL_USERS")
	else:
		print("ALREADY_IN_PORTAL_USERS")

	frappe.set_user(PORTAL_EMAIL)
	from erpnext.controllers.website_list_for_contact import get_transaction_list
	result = get_transaction_list("Quotation")
	print("REAL_PORTAL_LOGIC_RESULT:", [r.name for r in result])
	frappe.set_user("Administrator")
