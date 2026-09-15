import frappe


def run():
	est = frappe.get_doc("Print Estimate", "PE-Golden Arrow Printing & Packaging Co.-00018")
	n = est.apply_template()
	print("apply_template() callable, rows:", n)
	frappe.db.commit()
