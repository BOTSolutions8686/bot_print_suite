import frappe


def run():
	est = frappe.get_doc("Print Estimate", "PE-Golden Arrow Printing & Packaging Co.-00038")
	est.save(ignore_permissions=True)  # recompute with die-x-ups fix
	frappe.db.commit()

	print("Ups:", est.ups)
	for row in est.applied_cost_drivers:
		print(" ", row.cost_driver, "=", row.computed_cost)
	print("Cost Items Total:", est.driver_costs_total)
	print("Subtotal:", est.subtotal, "(Mofeed's real: 7825)")
	print("Gap:", round(est.subtotal - 7825, 2))
