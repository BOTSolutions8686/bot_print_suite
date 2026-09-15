import frappe


def run():
	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"product_template": "Folding Carton",
		"product_type": "Folding Carton",
		"finished_width_cm": 51, "finished_height_cm": 45,  # exactly as Mofeed gave it
		"quantity": 1000, "colours_front": 3, "colours_back": 0,
		"paper_type": "Ivory-350GSM",
		"sheet_size": "700x1000", "press": "Golden Arrow Offset",
		"bleed_mm": 0, "gutter_mm": 0,
		"die_width_cm": 53, "die_height_cm": 45,
		"glue_sides": 1,
		"margin_pct": 10,
	})
	est.insert(ignore_permissions=True)
	print("Finished W/H (mm, auto-computed):", est.finished_size_w, est.finished_size_h, "(should be 510, 450)")
	print("Sheets Required:", est.sheets_required, "(should be 600)")
	print("Sell Price:", est.sell_price, "(should be 2259.46)")
	frappe.db.commit()
