import frappe


def run():
	if frappe.db.exists("Web Form", "print-enquiry"):
		print("WEB_FORM_EXISTS")
		return

	frappe.get_doc({
		"doctype": "Web Form",
		"title": "Submit a Print Enquiry",
		"name": "print-enquiry",
		"route": "print-enquiry",
		"doc_type": "Print Enquiry",
		"module": "BOT Print Suite",
		"is_standard": 1,
		"published": 1,
		"login_required": 0,
		"allow_multiple": 1,
		"success_message": "Thank you - we've received your enquiry and will follow up shortly.",
		"web_form_fields": [
			{"fieldname": "customer", "fieldtype": "Link", "label": "Customer", "options": "Customer"},
			{"fieldname": "customer_name_new", "fieldtype": "Data", "label": "Company Name (if not yet a customer)"},
			{"fieldname": "contact_name", "fieldtype": "Data", "label": "Contact Name", "reqd": 1},
			{"fieldname": "phone", "fieldtype": "Data", "label": "Phone"},
			{"fieldname": "product_type", "fieldtype": "Select", "label": "Product Type",
			 "options": "\nFolding Carton\nCommercial\nLabel"},
			{"fieldname": "rough_spec", "fieldtype": "Text", "label": "Tell us about your job", "reqd": 1},
		],
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	print("WEB_FORM_CREATED")
