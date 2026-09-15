import frappe
from frappe.model.workflow import apply_workflow
from erpnext.selling.doctype.quotation.quotation import make_sales_order
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
from bot_print_suite.production.start_production import start_production
from bot_print_suite.production.job_tracker import get_job_tracker_data

CUSTOMER = "Golden Arrow Printing & Packaging Co."


def run():
	# 1. Link enquiry to customer, convert to estimate
	enq = frappe.get_doc("Print Enquiry", "ENQ-2026-00003")
	enq.customer = CUSTOMER
	enq.save(ignore_permissions=True)
	est_name = enq.make_print_estimate()
	print("STEP1_ESTIMATE:", est_name)

	# 2. Fill in the real spec (matches the enquiry: 20,000 A5 postcards, 4/4, 300gsm, gloss lam)
	est = frappe.get_doc("Print Estimate", est_name)
	est.finished_size_w = 148  # A5
	est.finished_size_h = 105
	est.quantity = 20000
	est.colours_front = 4
	est.colours_back = 4
	est.printing_method = "Sheetwise"
	est.ink_coverage = "Medium"
	est.substrate = "SBS Board"
	est.gsm = 300
	est.sheet_size = "700x1000"
	est.press = "Heidelberg SM74"
	est.append("finishing_operations", {
		"finishing_rate_card": frappe.db.get_value("Finishing Rate Card", {"operation": "Lamination"})
	})
	est.margin_pct = 20
	est.save(ignore_permissions=True)
	print("STEP2_SPEC_FILLED: sell_price =", est.sell_price)
	frappe.db.commit()
