import frappe

def run():
	est = frappe.get_doc("Print Estimate", "PE-Golden Arrow Printing & Packaging Co.-00002")
	qtn_name = est.create_quotation()
	qtn = frappe.get_doc("Quotation", qtn_name)
	print("SELL_PRICE (total):", est.sell_price)
	print("ITEM QTY:", qtn.items[0].qty, "RATE (per-unit):", qtn.items[0].rate)
	print("GRAND_TOTAL:", qtn.grand_total)
	frappe.db.commit()
