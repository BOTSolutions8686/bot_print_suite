import frappe


def run():
	enq = frappe.get_doc({
		"doctype": "Print Enquiry",
		"customer": "Test Golden Arrow",
		"contact_name": "Abdul Latif",
		"source": "Phone",
		"product_type": "Folding Carton",
		"rough_spec": "50,000 folding cartons, 4-colour, 300gsm board",
	})
	enq.insert(ignore_permissions=True)
	print("ENQUIRY_CREATED:", enq.name, "STATUS:", enq.status)

	estimate_name = enq.make_print_estimate()
	print("ESTIMATE_CREATED:", estimate_name)

	enq.reload()
	print("ENQUIRY_AFTER:", enq.status, enq.linked_estimate)

	est = frappe.get_doc("Print Estimate", estimate_name)
	print("ESTIMATE_ENQUIRY_LINK:", est.enquiry)
	print("ESTIMATE_CUSTOMER:", est.customer)
	print("ESTIMATE_PRODUCT_TYPE:", est.product_type)

	# Now fill in the rest and re-save to trigger real computation
	est.finished_size_w = 90
	est.finished_size_h = 55
	est.quantity = 10000
	est.colours_front = 4
	est.colours_back = 0
	est.sheet_size = "700x1000"
	est.press = "Test Heidelberg SM74"
	est.save(ignore_permissions=True)
	print("ESTIMATE_COMPUTED_UPS:", est.ups)
	print("ESTIMATE_COMPUTED_SELL_PRICE:", est.sell_price)

	frappe.db.commit()
