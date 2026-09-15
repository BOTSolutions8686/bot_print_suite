import frappe


def run():
	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"product_template": "Folding Carton",
		# NO product_type - auto-derived from template now
		"finished_width_cm": 51, "finished_height_cm": 45,
		"quantity": 1000, "colours_front": 3, "colours_back": 0,
		# NO printing_method, NO ink_coverage, NO bleed_mm/gutter_mm
		"paper_type": "Ivory-350GSM",
		"sheet_size": "70x100", "press": "Golden Arrow Offset",
		"die_width_cm": 53, "die_height_cm": 45,
		# NO die_cost, NO finishing_operations
		"glue_sides": 1,
		"margin_pct": 10,
	})
	est.insert(ignore_permissions=True)
	print("Product Type auto-set:", est.product_type)
	print("Sheets Required:", est.sheets_required, "(should be 600)")
	print("Subtotal:", est.subtotal, "(should be 2054.05)")
	print("Sell Price:", est.sell_price, "(should be 2259.46)")
	frappe.db.commit()
