import frappe


def run():
	est = frappe.get_doc("Print Estimate", "PE-Golden Arrow Printing & Packaging Co.-00038")
	est.save(ignore_permissions=True)  # trigger recompute with the new HTML builder
	frappe.db.commit()
	print(est.reconciliation_table_html)
