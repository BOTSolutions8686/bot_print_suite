import frappe


def run():
	est = frappe.get_doc("Print Estimate", "PE-Golden Arrow Printing & Packaging Co.-00040")
	est.save(ignore_permissions=True)
	frappe.db.commit()
	print(est.reconciliation_table_data)
