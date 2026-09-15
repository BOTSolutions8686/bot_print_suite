import frappe


def run():
	press = frappe.get_doc("Press Profile", "Golden Arrow Offset")
	press.run_waste_pct = 10
	press.save(ignore_permissions=True)
	print("Golden Arrow Offset waste % now:", press.run_waste_pct)
	frappe.db.commit()
