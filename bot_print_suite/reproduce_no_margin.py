import frappe


def run():
	# Margin % left completely unfilled (None), not even the string
	# default - testing whether THIS specific case still crashes
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
		# margin_pct deliberately omitted entirely
		# ink_coverage deliberately omitted entirely
	})
	est.insert(ignore_permissions=True)
	print("SUCCESS. Sell Price:", est.sell_price, "margin_pct was:", repr(est.margin_pct))
	frappe.db.commit()
