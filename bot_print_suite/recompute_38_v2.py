import frappe


def run():
	est = frappe.get_doc("Print Estimate", "PE-Golden Arrow Printing & Packaging Co.-00038")
	est.waste_pct_override = None  # press default is now correctly 10%
	est.save(ignore_permissions=True)

	print("Sheets Required:", est.sheets_required)
	print("Paper Cost:", est.paper_cost)
	for row in est.applied_cost_drivers:
		print(" ", row.cost_driver, "=", row.computed_cost)
	print("Cost Items Total:", est.driver_costs_total)
	print("Subtotal:", est.subtotal, "(Mofeed's real: 7825)")
	print("Gap:", round(est.subtotal - 7825, 2))
	frappe.db.commit()
