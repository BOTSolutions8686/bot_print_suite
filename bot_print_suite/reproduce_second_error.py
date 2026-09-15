import frappe


def run():
	# Exact field values from Talha's error report, reproduced precisely
	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"product_type": "Folding Carton",
		"colours_back": 0,
		"printing_method": "Sheetwise",
		"ink_coverage": "Medium",
		"finishing_operations": [],
		"bleed_mm": 3,
		"gutter_mm": 5,
		"quantity_breaks": [],
		"glue_sides": 0,
		"applied_cost_drivers": [],
		"margin_pct": "20",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"finished_size_w": 510,
		"finished_size_h": 450,
		"quantity": 1000,
		"product_template": "Folding Carton",
		"colours_front": 3,
		"substrate": "Ivory",
		"gsm": 350,
		"paper_type": "Ivory-350GSM",
		"sheet_size": "700x1000",
		"press": "Golden Arrow Offset",
	})
	est.insert(ignore_permissions=True)
	print("SUCCESS. Sell Price:", est.sell_price, "Rows:", len(est.applied_cost_drivers or []))
	frappe.db.commit()
