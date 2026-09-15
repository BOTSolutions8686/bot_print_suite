import frappe

def run():
	frappe.db.set_value("Quotation", "SAL-QTN-2026-00001", "contact_email", "abdullatif@goldenarrow-demo.example")
	frappe.db.commit()

	frappe.set_user("abdullatif@goldenarrow-demo.example")
	try:
		result = frappe.get_list("Quotation", fields=["name", "party_name", "contact_email"])
		print("AS_PORTAL_USER_AFTER_FIX:", result)
	except Exception as e:
		print("STILL_ERROR:", e)
	finally:
		frappe.set_user("Administrator")
