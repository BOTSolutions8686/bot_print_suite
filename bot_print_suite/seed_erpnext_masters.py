import frappe


def run():
	if not frappe.db.exists("Item Group", "All Item Groups"):
		frappe.get_doc({
			"doctype": "Item Group", "item_group_name": "All Item Groups",
			"is_group": 1,
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("Item Group", "Services"):
		frappe.get_doc({
			"doctype": "Item Group", "item_group_name": "Services",
			"parent_item_group": "All Item Groups", "is_group": 0,
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("UOM", "Nos"):
		frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)

	if not frappe.db.exists("Warehouse Type", "Transit"):
		frappe.get_doc({"doctype": "Warehouse Type", "name": "Transit"}).insert(ignore_permissions=True)

	if not frappe.db.exists("Price List", "Standard Selling"):
		frappe.get_doc({
			"doctype": "Price List", "price_list_name": "Standard Selling",
			"currency": "SAR", "selling": 1, "enabled": 1,
		}).insert(ignore_permissions=True)

	for set_name in ["Material Transfer for Manufacture", "Manufacture", "Material Issue", "Material Receipt"]:
		if not frappe.db.exists("Stock Entry Type", set_name):
			frappe.get_doc({"doctype": "Stock Entry Type", "name": set_name, "purpose": set_name, "is_standard": 1}).insert(ignore_permissions=True)
		else:
			frappe.db.set_value("Stock Entry Type", set_name, "is_standard", 1)

	frappe.db.commit()
	print("MASTERS_SEEDED")
