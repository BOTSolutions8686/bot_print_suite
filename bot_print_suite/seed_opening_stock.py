import frappe

def run():
	sr = frappe.get_doc({
		"doctype": "Stock Reconciliation",
		"purpose": "Stock Reconciliation",
		"expense_account": "Temporary Opening - GAP",
		"company": frappe.defaults.get_global_default("company"),
		"items": [
			{"item_code": "PAPER-SBS-BOARD-300GSM", "warehouse": "Stores - GAP", "qty": 2000, "valuation_rate": 3},
			{"item_code": "PLATE-STD", "warehouse": "Stores - GAP", "qty": 50, "valuation_rate": 45},
		],
	})
	sr.insert(ignore_permissions=True)
	sr.submit()
	print("STOCK_RECONCILIATION_SUBMITTED:", sr.name)
	frappe.db.commit()
