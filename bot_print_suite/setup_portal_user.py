import frappe

CUSTOMER = "Golden Arrow Printing & Packaging Co."
PORTAL_EMAIL = "abdullatif@goldenarrow-demo.example"
PORTAL_PASSWORD = "GoldenArrow!2026Print"


def run():
	if not frappe.db.exists("User", PORTAL_EMAIL):
		user = frappe.get_doc({
			"doctype": "User",
			"email": PORTAL_EMAIL,
			"first_name": "Abdul",
			"last_name": "Latif",
			"send_welcome_email": 0,
			"user_type": "Website User",
			"roles": [{"role": "Customer"}],
		})
		user.insert(ignore_permissions=True)
		user.new_password = PORTAL_PASSWORD
		user.save(ignore_permissions=True)
		print("USER_CREATED:", user.name)
	else:
		print("USER_EXISTS")

	if not frappe.db.exists("Contact", {"email_id": PORTAL_EMAIL}):
		contact = frappe.get_doc({
			"doctype": "Contact",
			"first_name": "Abdul",
			"last_name": "Latif",
			"email_ids": [{"email_id": PORTAL_EMAIL, "is_primary": 1}],
			"links": [{"link_doctype": "Customer", "link_name": CUSTOMER}],
			"user": PORTAL_EMAIL,
		})
		contact.insert(ignore_permissions=True)
		print("CONTACT_CREATED:", contact.name)
	else:
		print("CONTACT_EXISTS")

	# Link this contact as the customer's primary contact (nice-to-have,
	# not what actually gates portal visibility)
	frappe.db.set_value("Customer", CUSTOMER, "customer_primary_contact",
		frappe.db.get_value("Contact", {"email_id": PORTAL_EMAIL}, "name"))

	# THE ACTUAL mechanism that gates whether this user sees the
	# Customer's Quotations/Orders on the portal - confirmed by reading
	# erpnext/controllers/website_list_for_contact.py directly, not
	# assumed. Neither the Contact link above nor a Custom DocPerm role
	# permission is what the real /quotations and /orders pages check;
	# they call get_customers_suppliers(), which queries this child
	# table on Customer, then sets ignore_permissions=True once a match
	# is found. Skipping this step is the actual reason a portal user
	# sees "Nothing to show" even with a real Contact and real documents.
	customer = frappe.get_doc("Customer", CUSTOMER)
	if PORTAL_EMAIL not in [pu.user for pu in customer.get("portal_users", [])]:
		customer.append("portal_users", {"user": PORTAL_EMAIL})
		customer.save(ignore_permissions=True)
		print("ADDED_TO_CUSTOMER_PORTAL_USERS")

	# Also add explicit Customer-role read on Quotation/Sales Order.
	# Stock ERPNext ships ZERO Role Permission rows for "Customer" role on
	# these doctypes - confirmed by direct DocPerm query. The real portal
	# page bypasses this via ignore_permissions=True once portal_users
	# matches, so this isn't strictly required for /quotations or /orders
	# themselves, but IS needed for any other path that respects standard
	# permissions (API access, our own future portal work) - kept as
	# defense in depth, not redundant.
	for doctype in ["Quotation", "Sales Order"]:
		if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": "Customer"}):
			frappe.get_doc({
				"doctype": "Custom DocPerm", "parent": doctype, "parenttype": "DocType",
				"parentfield": "permissions", "role": "Customer", "read": 1, "if_owner": 0,
			}).insert(ignore_permissions=True)

	frappe.db.commit()
	print("DONE. Login as:", PORTAL_EMAIL, "/", PORTAL_PASSWORD)
