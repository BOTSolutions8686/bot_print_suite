import frappe


def run():
	est = frappe.get_doc("Print Estimate", "PE-Test Golden Arrow-00003")
	print("BEFORE:", frappe.db.get_value("Print Enquiry", est.enquiry, "status"))

	qtn_name = est.create_quotation()
	print("QUOTATION_CREATED:", qtn_name)
	print("AFTER_QUOTE:", frappe.db.get_value("Print Enquiry", est.enquiry, "status"))

	qtn = frappe.get_doc("Quotation", qtn_name)
	print("QTN_LINKED_ESTIMATE:", qtn.custom_print_estimate)
	print("QTN_ITEM_RATE:", qtn.items[0].rate, "QTY:", qtn.items[0].qty)

	# simulate the quotation being marked Ordered (won)
	qtn.db_set("status", "Ordered")
	qtn.run_method("on_update")
	print("AFTER_WON:", frappe.db.get_value("Print Enquiry", est.enquiry, "status"))

	frappe.db.commit()
