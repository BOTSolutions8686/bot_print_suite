import frappe
from frappe.desk.doctype.number_card.number_card import get_result


def run():
	for name in ["Open Enquiries", "Estimates Pending", "Quotes Awaiting Approval", "Jobs in Production"]:
		card = frappe.get_doc("Number Card", name)
		result = get_result(card.as_dict(), card.filters_json)
		print(f"{name}: {result}")

	for name in ["Jobs Due This Week", "Overdue Jobs"]:
		card = frappe.get_doc("Number Card", name)
		method_result = frappe.call(card.method)
		print(f"{name}: {method_result}")
