import frappe


def run():
	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"product_type": "Folding Carton",
		"product_template": "Folding Carton",
		"finished_size_w": 510, "finished_size_h": 450,
		"quantity": 1000,
		"colours_front": 3, "colours_back": 0,
		"printing_method": "Sheetwise", "ink_coverage": "Medium",
		"substrate": "Ivory", "gsm": 350, "paper_type": "Ivory-350GSM",
		"sheet_size": "700x1000", "press": "Golden Arrow Offset",
		"margin_pct": "20",  # STRING, exactly reproducing Talha's real crash
	})
	est.insert(ignore_permissions=True)
	print("SUCCESS, no crash. Sell Price:", est.sell_price)
	frappe.db.commit()
