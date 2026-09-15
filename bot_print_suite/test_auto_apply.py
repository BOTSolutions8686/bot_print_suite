import frappe


def run():
	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"product_type": "Folding Carton",
		"product_template": "Folding Carton",  # picked as part of the form, nothing else
		"finished_size_w": 510, "finished_size_h": 450,
		"quantity": 1000, "colours_front": 3, "colours_back": 0,
		"printing_method": "Sheetwise", "ink_coverage": "Medium",
		"paper_type": "Ivory-350GSM",
		"sheet_size": "700x1000", "press": "Golden Arrow Offset",
		"bleed_mm": 0, "gutter_mm": 0,
		"die_area_cm2": 53 * 45, "glue_sides": 1,
		"margin_pct": "20",  # STRING, matching a real fresh-form default
	})
	est.insert(ignore_permissions=True)  # ONE save, no separate apply_template() call
	print("Rows auto-applied on first save:", len(est.applied_cost_drivers or []))
	for row in est.applied_cost_drivers:
		print("  ", row.cost_driver, "=", row.computed_cost)
	print("Sell Price:", est.sell_price)
	frappe.db.commit()
