import frappe


def run():
	# Test 1: die width/height, NOT area - should auto-compute to 2385
	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"product_template": "Folding Carton",
		"product_type": "Folding Carton",
		"finished_size_w": 510, "finished_size_h": 450,
		"quantity": 1000, "colours_front": 3, "colours_back": 0,
		"paper_type": "Ivory-350GSM",
		"sheet_size": "700x1000", "press": "Golden Arrow Offset",
		"bleed_mm": 0, "gutter_mm": 0,
		"die_width_cm": 53, "die_height_cm": 45,  # NOT die_area_cm2 directly
		"glue_sides": 1,
		"margin_pct": 10,
	})
	est.insert(ignore_permissions=True)
	print("Die area auto-computed:", est.die_area_cm2, "(should be 2385)")
	for row in est.applied_cost_drivers:
		if "Die" in row.cost_driver or "Glue" in row.cost_driver:
			print(" ", row.cost_driver, "=", row.computed_cost)
	print("Sell Price (1 glue side):", est.sell_price)

	# Test 2: same job but 2 glue sides - should cost MORE now
	est2 = frappe.copy_doc(est)
	est2.glue_sides = 2
	est2.applied_cost_drivers = []  # force recompute
	est2.insert(ignore_permissions=True)
	for row in est2.applied_cost_drivers:
		if "Glue" in row.cost_driver:
			print("Glue (2 sides) =", row.computed_cost, "(should be 300, double of 150)")
	print("Sell Price (2 glue sides):", est2.sell_price, "(should be MORE than 1-side version)")

	frappe.db.commit()
