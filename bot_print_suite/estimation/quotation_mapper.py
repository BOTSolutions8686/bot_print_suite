import frappe
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_quotation(estimate_name, qty=None):
	"""Maps a Print Estimate (or one of its quantity-break rows) into a
	stock ERPNext Quotation. Thin by design - PLAN.md section 3: 'No
	custom doctype. Standard ERPNext Quotation, populated from the Print
	Estimate.' Approval is handled entirely by the Quotation Approval
	workflow (native Frappe Workflow config), not by code here.
	"""
	est = frappe.get_doc("Print Estimate", estimate_name)
	qty = frappe.utils.cint(qty) if qty else est.quantity

	if qty == est.quantity:
		sell_price = est.sell_price
	else:
		row = next((r for r in est.computed_breaks if r.qty == qty), None)
		if not row:
			frappe.throw(f"No computed result for quantity {qty} on this estimate.")
		sell_price = row.sell_price

	quotation = frappe.new_doc("Quotation")
	quotation.quotation_to = "Customer"
	quotation.party_name = est.customer
	quotation.company = frappe.defaults.get_global_default("company")
	quotation.currency = "SAR"
	quotation.conversion_rate = 1
	quotation.selling_price_list = "Standard Selling"
	quotation.price_list_currency = "SAR"
	quotation.plc_conversion_rate = 1
	quotation.custom_print_estimate = est.name
	# sell_price is the TOTAL price for the whole job/batch (that's what the
	# estimate computes and what the estimator/customer actually sees and
	# agrees to). ERPNext's Quotation Item does qty x rate = amount, so rate
	# here must be the PER-UNIT price (sell_price / qty), not sell_price
	# itself - passing sell_price directly as rate with qty=10000 would
	# silently multiply the total by 10000. Caught via real browser
	# verification: a job that should total ~1,022 SAR showed as a
	# 10.2 MILLION SAR grand total on the actual Sales Order.
	per_unit_rate = flt(sell_price) / qty if qty else 0
	quotation.append("items", {
		"item_code": _get_or_create_placeholder_item(est),
		"qty": qty,
		"rate": per_unit_rate,
	})
	return quotation


def _get_or_create_placeholder_item(est):
	"""Full auto-creation of the real finished-good Item is PLAN.md 4d
	(Zero-friction production chain) - out of scope for step 4. For now,
	map to a generic per-product-type service item so the Quotation can be
	created; 4d replaces this with a proper per-job Item."""
	code = f"PRINT-JOB-{est.product_type.upper().replace(' ', '-')}"
	if not frappe.db.exists("Item", code):
		frappe.get_doc({
			"doctype": "Item",
			"item_code": code,
			"item_name": f"Print Job - {est.product_type}",
			"item_group": "Services",
			"stock_uom": "Nos",
			"is_stock_item": 0,
		}).insert(ignore_permissions=True)
	return code
