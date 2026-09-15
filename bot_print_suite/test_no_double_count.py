import frappe


def run():
	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"product_template": "Folding Carton",
		"product_type": "Folding Carton",
		"finished_size_w": 510, "finished_size_h": 450,
		"quantity": 1000, "colours_front": 3, "colours_back": 0,
		"printing_method": "Sheetwise",
		"paper_type": "Ivory-350GSM",
		"sheet_size": "700x1000", "press": "Golden Arrow Offset",
		"bleed_mm": 0, "gutter_mm": 0,
		"die_area_cm2": 53 * 45,
		"die_cost": 999,  # deliberately also fill in the OLD field - should be IGNORED for templated
		"margin_pct": 10,
	})
	est.insert(ignore_permissions=True)
	print("Subtotal:", est.subtotal, "(should be 2054.05, NOT 2054.05+999)")
	print("Sell Price:", est.sell_price, "(should be 2259.46)")
	frappe.db.commit()
