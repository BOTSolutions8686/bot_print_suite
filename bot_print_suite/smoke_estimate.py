import frappe


def run():
	doc = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Test Golden Arrow",
		"product_type": "Folding Carton",
		"finished_size_w": 90,
		"finished_size_h": 55,
		"quantity": 10000,
		"colours_front": 4,
		"colours_back": 4,
		"printing_method": "Sheetwise",
		"ink_coverage": "Medium",
		"substrate": "SBS Board",
		"gsm": 300,
		"sheet_size": "700x1000",
		"press": "Test Heidelberg SM74",
		"bleed_mm": 3,
		"gutter_mm": 5,
		"die_cost": 50,
		"freight_cost": 100,
		"margin_pct": 20,
		"finishing_operations": [
			{"finishing_rate_card": frappe.db.get_value("Finishing Rate Card", {"operation": "Lamination"})},
		],
		"quantity_breaks": [{"qty": 20000}],
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	print("ESTIMATE_NAME:", doc.name)
	print("UPS:", doc.ups)
	print("SHEETS_REQUIRED:", doc.sheets_required)
	print("PAPER_COST:", doc.paper_cost)
	print("PLATE_COST:", doc.plate_cost)
	print("PRESS_RUN_COST:", doc.press_run_cost)
	print("INK_COST:", doc.ink_cost)
	print("FINISHING_COST_TOTAL:", doc.finishing_cost_total)
	print("SUBTOTAL:", doc.subtotal)
	print("SELL_PRICE:", doc.sell_price)
	print("FINISHING_ROW_COST:", doc.finishing_operations[0].computed_cost)
	print("BREAK_ROWS:", len(doc.computed_breaks))
	for r in doc.computed_breaks:
		print("  BREAK:", r.qty, r.sheets_required, r.subtotal, r.sell_price)
