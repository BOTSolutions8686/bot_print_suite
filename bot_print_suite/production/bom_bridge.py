"""
BOT Print Suite - Estimate to per-job BOM bridge (PLAN.md section 4b).

Maps a Job Order's already-computed Print Estimate quantities into a real
ERPNext BOM. Deliberately a MAPPING function, not new calculation logic -
every quantity here was already computed by estimation/engine.py and is
just being read off the Print Estimate document.

The job-specific finished-good Item is assigned to the Quotation before it
is submitted. ERPNext's native mapper then carries it into the Sales Order,
so this bridge never mutates submitted commercial documents.
"""

import frappe
from frappe.utils import flt
from bot_print_suite.estimation.engine import compute_plates

_PAPER_ITEM_GROUP = "Raw Material"
_PLATE_ITEM_CODE = "PLATE-STD"

# Canonical operation sequence (PLAN.md 4d) + a pragmatic MVP mapping of
# each finishing operation to a physical workstation. Several finishing
# ops sharing "Laminator" is a simplification for now, not a real routing
# engine - fine for Phase 1, worth revisiting if a client's shop floor
# actually separates these onto distinct machines.
_CANONICAL_FINISHING_ORDER = ["Lamination", "Foiling", "Embossing", "UV Coating", "Die-cut", "Gluing", "Packing"]
_FINISHING_WORKSTATION = {
	"Lamination": "Laminator", "Foiling": "Laminator", "Embossing": "Laminator",
	"UV Coating": "Laminator", "Die-cut": "Die-Cutter", "Gluing": "Gluer",
	"Packing": "Packing",
}
_COST_DRIVER_TO_FINISHING = {
	"lamination": "Lamination",
	"foil": "Foiling",
	"emboss": "Embossing",
	"uv": "UV Coating",
	"die": "Die-cut",
	"cutting": "Die-cut",
	"glue": "Gluing",
	"pack": "Packing",
}

_NON_OPERATION_DRIVERS = ("paper", "plate")


def get_estimate_for_sales_order(sales_order_name):
	"""Sales Order -> its first item's originating Quotation
	(prevdoc_docname) -> that Quotation's linked Print Estimate."""
	so_item = frappe.db.get_value(
		"Sales Order Item", {"parent": sales_order_name}, "prevdoc_docname"
	)
	if not so_item:
		return None
	return frappe.db.get_value("Quotation", so_item, "custom_print_estimate")


def _ensure_item_group(name, parent="All Item Groups"):
	if not frappe.db.exists("Item Group", name):
		frappe.get_doc({
			"doctype": "Item Group", "item_group_name": name,
			"parent_item_group": parent, "is_group": 0,
		}).insert(ignore_permissions=True)
	return name


def _get_or_create_paper_item(est):
	code = f"PAPER-{est.substrate}-{int(est.gsm)}GSM".upper().replace(" ", "-")
	if not frappe.db.exists("Item", code):
		_ensure_item_group(_PAPER_ITEM_GROUP)
		frappe.get_doc({
			"doctype": "Item", "item_code": code,
			"item_name": f"{est.substrate} {int(est.gsm)}GSM",
			"item_group": _PAPER_ITEM_GROUP, "stock_uom": "Nos",
			"is_stock_item": 1,
		}).insert(ignore_permissions=True)
	return code


def _get_or_create_plate_item():
	if not frappe.db.exists("Item", _PLATE_ITEM_CODE):
		_ensure_item_group(_PAPER_ITEM_GROUP)
		frappe.get_doc({
			"doctype": "Item", "item_code": _PLATE_ITEM_CODE,
			"item_name": "Printing Plate (Standard)",
			"item_group": _PAPER_ITEM_GROUP, "stock_uom": "Nos",
			"is_stock_item": 1,
		}).insert(ignore_permissions=True)
	return _PLATE_ITEM_CODE


def _set_planned_buying_rate(item_code, rate):
	"""Store the estimate's planned raw-material rate in Standard Buying."""
	price_list = "Standard Buying"
	name = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": price_list}, "name")
	if name:
		frappe.db.set_value("Item Price", name, "price_list_rate", flt(rate))
	else:
		frappe.get_doc({
			"doctype": "Item Price", "item_code": item_code,
			"price_list": price_list, "price_list_rate": flt(rate), "buying": 1,
		}).insert(ignore_permissions=True)


def _ensure_bom_rate_precision():
	"""Paper is priced per sheet, so two-decimal BOM rates distort large runs."""
	filters = {
		"doc_type": "BOM Item", "field_name": "rate", "property": "precision",
	}
	if not frappe.db.exists("Property Setter", filters):
		frappe.get_doc({
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": "BOM Item",
			"field_name": "rate",
			"property": "precision",
			"value": "4",
			"property_type": "Int",
		}).insert(ignore_permissions=True)
		frappe.clear_cache(doctype="BOM Item")


def _ensure_operation_and_workstation(operation, workstation):
	if not frappe.db.exists("Operation", operation):
		frappe.get_doc({"doctype": "Operation", "name": operation, "description": operation}).insert(ignore_permissions=True)
	if not frappe.db.exists("Workstation", workstation):
		frappe.get_doc({"doctype": "Workstation", "workstation_name": workstation, "production_capacity": 1}).insert(ignore_permissions=True)


def _planned_operation_costs(est):
	"""Map estimate cost rows to the physical BOM operation that incurs them."""
	costs = {"CTP": 0.0, "Press": 0.0}
	for row in est.get("applied_cost_drivers") or []:
		if not row.enabled:
			continue
		name = (row.cost_driver or "").lower()
		if any(keyword in name for keyword in _NON_OPERATION_DRIVERS):
			continue
		operation = None
		if "artwork" in name:
			operation = "CTP"
		elif "printing" in name or "press" in name:
			operation = "Press"
		else:
			for keyword, candidate in _COST_DRIVER_TO_FINISHING.items():
				if keyword in name:
					operation = candidate
					break
		if operation:
			costs[operation] = flt(costs.get(operation)) + flt(row.computed_cost)
	return costs


def _derive_operations(est):
	"""Routing derived from the estimate (PLAN.md 4d): press selection ->
	press operation, finishing checkboxes -> finishing operations in
	canonical sequence. Returns a list of (operation, workstation) tuples
	ready to append to a BOM's operations table."""
	ops = [("CTP", "CTP"), ("Press", est.press)]

	# Backward-compatible with early estimates that used a dedicated
	# Finishing Operations table, while current estimates represent these
	# choices as enabled Cost Items.
	present = {
		row.finishing_rate_card and frappe.db.get_value(
			"Finishing Rate Card", row.finishing_rate_card, "operation"
		)
		for row in (est.get("finishing_operations") or [])
	}
	for row in est.get("applied_cost_drivers") or []:
		if not row.enabled:
			continue
		name = (row.cost_driver or "").lower()
		for keyword, operation in _COST_DRIVER_TO_FINISHING.items():
			if keyword in name:
				present.add(operation)
				break
	for op_name in _CANONICAL_FINISHING_ORDER:
		if op_name in present:
			ops.append((op_name, _FINISHING_WORKSTATION[op_name]))
	return ops


def create_job_bom(sales_order_name):
	"""Creates and submits a BOM for this job from its linked estimate's
	already-computed quantities, with a routing derived from the estimate.
	Returns the BOM name."""
	est_name = get_estimate_for_sales_order(sales_order_name)
	if not est_name:
		frappe.throw(f"No linked Print Estimate found for {sales_order_name}.")
	est = frappe.get_doc("Print Estimate", est_name)
	so = frappe.get_doc("Sales Order", sales_order_name)

	production_item = frappe.db.get_value(
		"Sales Order Item", {"parent": sales_order_name}, "item_code"
	)
	if not production_item:
		frappe.throw(f"No production Item found on {sales_order_name}.")
	if not frappe.db.get_value("Item", production_item, "is_stock_item"):
		frappe.throw(
			f"Item {production_item} on {sales_order_name} is not a stock Item. "
			"Submit its source Quotation again after installing the latest BOT Print Suite update."
		)
	paper_item = _get_or_create_paper_item(est)
	plate_item = _get_or_create_plate_item()
	_ensure_bom_rate_precision()
	plate_count = compute_plates(est.colours_front, est.colours_back, "Sheetwise")
	plate_cost = next((flt(row.computed_cost) for row in est.applied_cost_drivers
		if row.enabled and "plate" in (row.cost_driver or "").lower()), 0)
	paper_rate = flt(est.paper_cost) / flt(est.sheets_required)
	_set_planned_buying_rate(paper_item, paper_rate)
	if plate_count:
		plate_rate = plate_cost / plate_count
		_set_planned_buying_rate(plate_item, plate_rate)
	planned_operation_costs = _planned_operation_costs(est)

	bom = frappe.new_doc("BOM")
	bom.item = production_item
	bom.quantity = est.quantity
	bom.company = so.company
	bom.rm_cost_as_per = "Price List"
	bom.buying_price_list = "Standard Buying"
	bom.append("items", {"item_code": paper_item, "qty": est.sheets_required, "uom": "Nos"})
	if plate_count:
		bom.append("items", {"item_code": plate_item, "qty": plate_count, "uom": "Nos"})

	bom.with_operations = 1
	for operation, workstation in _derive_operations(est):
		_ensure_operation_and_workstation(operation, workstation)
		hour_rate = flt(planned_operation_costs.get(operation))
		bom.append("operations", {
			"operation": operation, "workstation": workstation,
			"time_in_mins": 60, "hour_rate": hour_rate, "fixed_time": 1,
		})

	bom.insert(ignore_permissions=True)
	bom.submit()
	_reconcile_material_amounts(bom, paper_item, flt(est.paper_cost), plate_item, plate_cost)

	frappe.db.set_value("Sales Order", sales_order_name, "custom_job_status", "Prepress")
	return bom.name


def _reconcile_material_amounts(bom, paper_item, paper_cost, plate_item, plate_cost):
	"""Keep planned paper/plate totals exact despite Currency-rate rounding.

	ERPNext rounds a BOM Item's unit rate before multiplying very large sheet
	quantities.  The quantity must stay exact for purchasing and stock transfer,
	so we persist the approved estimate amount on the planning BOM instead of
	moving the rounding difference into an unrelated operation.
	"""
	conversion_rate = flt(bom.conversion_rate) or 1
	planned = {paper_item: paper_cost, plate_item: plate_cost}
	material_total = 0
	for row in bom.items:
		amount = flt(planned.get(row.item_code, row.amount))
		material_total += amount
		frappe.db.set_value("BOM Item", row.name, {
			"amount": amount,
			"base_amount": amount * conversion_rate,
		}, update_modified=False)
	total_cost = material_total + flt(bom.operating_cost) - flt(bom.secondary_items_cost)
	frappe.db.set_value("BOM", bom.name, {
		"raw_material_cost": material_total,
		"base_raw_material_cost": material_total * conversion_rate,
		"total_cost": total_cost,
		"base_total_cost": total_cost * conversion_rate,
	}, update_modified=False)
	bom.reload()
