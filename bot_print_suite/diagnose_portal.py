import frappe

def run():
	frappe.set_user("abdullatif@goldenarrow-demo.example")
	try:
		result = frappe.get_list("Quotation", fields=["name", "party_name", "docstatus"])
		print("AS_PORTAL_USER:", result)
	except Exception as e:
		print("ERROR:", e)
	finally:
		frappe.set_user("Administrator")

	# Also check what the actual quotation doc looks like
	qtn = frappe.db.get_value("Quotation", {"docstatus": 1}, ["name", "quotation_to", "party_name", "contact_email"], as_dict=True)
	print("REAL_QUOTATION:", qtn)
