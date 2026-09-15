"""
BOT Print Suite - Estimate to per-job BOM bridge (PLAN.md section 4b).

Maps a Job Order's already-computed Print Estimate quantities into a real
ERPNext BOM. Deliberately a MAPPING function, not new calculation logic -
every quantity here was already computed by estimation/engine.py and is
just being read off the Print Estimate document.

Scope note: creating a per-job finished-good Item is pulled forward from
step 7 (4d) because a per-job BOM structurally needs a per-job Item (the
Quotation-stage placeholder item from quotation_mapper.py is shared across
all jobs of the same product type, which is fine for pricing but wrong for
a specific job's BOM). Only that one piece is pulled forward - routing
derivation, the Start Production button, and backflush config remain 4d.
"""

import frappe

_PAPER_ITEM_GROUP = "Raw Material"
_PLATE_ITEM_CODE = "PLATE-STD"

# Canonical operation sequence (PLAN.md 4d) + a pragmatic MVP mapping of
# each finishing operation to a physical workstation. Several finishing
# ops sharing "Laminator" is a simplification for now, not a real routing
# engine - fine for Phase 1, worth revisiting if a client's shop floor
# actually separates these onto distinct machines.
_CANONICAL_FINISHING_ORDER = ["Lamination", "Foiling", "Embossing", "UV Coating", "Die-cut", "Gluing"]
_FINISHING_WORKSTATION = {
	"Lamination": "Laminator", "Foiling": "Laminator", "Embossing": "Laminator",
	"UV Coating": "Laminator", "Die-cut": "Die-Cutter", "Gluing": "Gluer",
}
_PLACEHOLDER_OP_MINUTES = 30


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


def _get_or_create_job_item(sales_order_name, est):
	"""Per-job finished-good Item - pulled forward from 4d for the reason
	documented at module level. Code is job-specific, not shared."""
	code = f"JOB-{sales_order_name}"
	if not frappe.db.exists("Item", code):
		frappe.get_doc({
			"doctype": "Item", "item_code": code,
			"item_name": f"{est.product_type} - {sales_order_name}",
			"item_group": _ensure_item_group("Finished Job"),
			"stock_uom": "Nos", "is_stock_item": 1,
		}).insert(ignore_permissions=True)
	return code


def _derive_operations(est):
	"""Routing derived from the estimate (PLAN.md 4d): press selection ->
	press operation, finishing checkboxes -> finishing operations in
	canonical sequence. Returns a list of (operation, workstation) tuples
	ready to append to a BOM's operations table."""
	ops = [("CTP", "CTP"), ("Press", est.press)]

	present = {row.finishing_rate_card and frappe.db.get_value(
		"Finishing Rate Card", row.finishing_rate_card, "operation") for row in (est.finishing_operations or [])}
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

	production_item = _get_or_create_job_item(sales_order_name, est)
	paper_item = _get_or_create_paper_item(est)
	plate_item = _get_or_create_plate_item()

	# The Sales Order carries the generic quotation-stage placeholder item
	# (correct for pricing across many jobs of the same product type - see
	# quotation_mapper.py). Now that this job has its own BOM, it needs
	# its own Item, and ERPNext's Work Order requires production_item to
	# match a line on the Sales Order - so swap it here, the moment a job
	# stops being "any folding carton" and becomes *this* job. Direct
	# db.set_value on a submitted document's child row is deliberate: this
	# is a controlled system correction, not a user edit.
	so_item_name = frappe.db.get_value("Sales Order Item", {"parent": sales_order_name}, "name")
	frappe.db.set_value("Sales Order Item", so_item_name, "item_code", production_item)
	frappe.db.set_value("Sales Order Item", so_item_name, "item_name", production_item)

	bom = frappe.new_doc("BOM")
	bom.item = production_item
	bom.quantity = est.quantity
	bom.company = so.company
	bom.append("items", {"item_code": paper_item, "qty": est.sheets_required, "uom": "Nos"})
	if est.plates_count:
		bom.append("items", {"item_code": plate_item, "qty": est.plates_count, "uom": "Nos"})

	bom.with_operations = 1
	for operation, workstation in _derive_operations(est):
		hour_rate = frappe.db.get_value("Workstation", workstation, "hour_rate") or 0
		bom.append("operations", {
			"operation": operation, "workstation": workstation,
			"time_in_mins": _PLACEHOLDER_OP_MINUTES, "hour_rate": hour_rate,
		})

	bom.insert(ignore_permissions=True)
	bom.submit()

	frappe.db.set_value("Sales Order", sales_order_name, "custom_job_status", "Prepress")
	return bom.name
