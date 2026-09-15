import frappe


def run():
	est = frappe.get_doc("Print Estimate", "PE-Golden Arrow Printing & Packaging Co.-00021")
	est.die_area_cm2 = 53 * 45
	est.save(ignore_permissions=True)
	print("Fixed. Subtotal:", est.subtotal, "Sell Price:", est.sell_price)
	frappe.db.commit()
