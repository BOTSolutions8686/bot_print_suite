import frappe


def run():
	for op in ["CTP", "Press", "Lamination", "Foiling", "Embossing", "UV Coating", "Die-cut", "Gluing"]:
		if not frappe.db.exists("Operation", op):
			frappe.get_doc({"doctype": "Operation", "name": op, "operation_name": op}).insert(ignore_permissions=True)

	for ws in ["CTP", "Laminator", "Die-Cutter", "Gluer"]:
		if not frappe.db.exists("Workstation", ws):
			frappe.get_doc({"doctype": "Workstation", "workstation_name": ws, "hour_rate": 50}).insert(ignore_permissions=True)

	for press in frappe.get_all("Press Profile", fields=["name"]):
		if not frappe.db.exists("Workstation", press.name):
			frappe.get_doc({"doctype": "Workstation", "workstation_name": press.name, "hour_rate": 100}).insert(ignore_permissions=True)

	frappe.db.commit()
	print("ROUTING_MASTERS_SEEDED")
