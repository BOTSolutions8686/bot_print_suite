"""
BOT Print Suite - "Start Production" one-click action (PLAN.md 4d).

Chains: ensure BOM exists (via bom_bridge) -> prepare a draft Work Order
(this is where block_production_without_approved_artwork actually fires)
-> prepare either a draft Material Request for shortages or, after a human
submits the Work Order, a draft Material Transfer for review.  Operational
documents deliberately stay draft until a person approves them, consistent
with the design principle in PLAN.md 4d:
"the app GENERATES standard ERPNext documents, it never replaces them").
"""

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
from bot_print_suite.production.bom_bridge import create_job_bom
from bot_print_suite.production.bom_bridge import get_estimate_for_sales_order


@frappe.whitelist()
def start_production(sales_order_name):
	so = frappe.get_doc("Sales Order", sales_order_name)
	so.check_permission("write")
	_require_permission("BOM", "create")
	_require_permission("Work Order", "create")

	existing_work_order = frappe.db.get_value(
		"Work Order",
		{"sales_order": sales_order_name, "docstatus": ["<", 2]},
		"name",
	)
	if existing_work_order:
		work_order = frappe.get_doc("Work Order", existing_work_order)
		bom = frappe.get_doc("BOM", work_order.bom_no)
		abbr = frappe.db.get_value("Company", so.company, "abbr")
		stores_warehouse = f"Stores - {abbr}"
		material_transfer = frappe.db.get_value(
			"Stock Entry",
			{
				"work_order": existing_work_order,
				"stock_entry_type": "Material Transfer for Manufacture",
				"docstatus": ["<", 2],
			},
			"name",
		)
		material_request = frappe.db.get_value(
			"Material Request Item", {"sales_order": sales_order_name, "docstatus": ["<", 2]}, "parent"
		)
		shortages = _get_shortages(bom, stores_warehouse)
		unvalued_items = _get_unvalued_items(bom, stores_warehouse)
		if shortages and not material_request:
			_require_permission("Material Request", "create")
			material_request = _make_material_request(so, shortages, stores_warehouse).name
		elif not shortages and not unvalued_items and work_order.docstatus == 1 and not material_transfer:
			_require_permission("Stock Entry", "create")
			material_transfer = _make_material_transfer(work_order.name, stores_warehouse).name
		return _result(so, existing_work_order, material_transfer, material_request, True)

	production_item = frappe.db.get_value(
		"Sales Order Item", {"parent": sales_order_name}, "item_code"
	)
	bom_name = frappe.db.get_value("BOM", {"item": production_item, "docstatus": 1})
	if not bom_name:
		bom_name = create_job_bom(sales_order_name)

	bom = frappe.get_doc("BOM", bom_name)

	work_order = frappe.new_doc("Work Order")
	work_order.production_item = bom.item
	work_order.bom_no = bom.name
	work_order.qty = bom.quantity
	work_order.company = so.company
	work_order.sales_order = so.name
	work_order.planned_start_date = frappe.utils.now_datetime()
	abbr = frappe.db.get_value("Company", so.company, "abbr")
	work_order.wip_warehouse = f"Work In Progress - {abbr}"
	work_order.fg_warehouse = f"Finished Goods - {abbr}"
	work_order.insert(ignore_permissions=True)  # validate hook fires here

	stores_warehouse = f"Stores - {abbr}"
	shortages = _get_shortages(bom, stores_warehouse)
	material_request = None
	material_transfer = None
	if shortages:
		_require_permission("Material Request", "create")
		material_request = _make_material_request(so, shortages, stores_warehouse)
	# A stock transfer requires a submitted Work Order.  On the first click
	# the Work Order is deliberately draft so a production supervisor reviews
	# and releases it before inventory can move.

	return _result(
		so, work_order.name,
		material_transfer.name if material_transfer else None,
		material_request.name if material_request else None,
		False,
	)


def _get_shortages(bom, warehouse):
	shortages = []
	for row in bom.items:
		available = frappe.db.get_value(
			"Bin", {"item_code": row.item_code, "warehouse": warehouse}, "actual_qty"
		) or 0
		shortage = max(frappe.utils.flt(row.qty) - frappe.utils.flt(available), 0)
		if shortage:
			shortages.append({"item_code": row.item_code, "qty": shortage})
	return shortages


def _get_unvalued_items(bom, warehouse):
	"""Return materials physically present but still carrying no stock value."""
	items = []
	for row in bom.items:
		stock = frappe.db.get_value(
			"Bin", {"item_code": row.item_code, "warehouse": warehouse},
			["actual_qty", "valuation_rate"], as_dict=True,
		) or {}
		if frappe.utils.flt(stock.get("actual_qty")) >= frappe.utils.flt(row.qty) and not frappe.utils.flt(stock.get("valuation_rate")):
			items.append(row.item_code)
	return items


def _make_material_request(sales_order, shortages, warehouse):
	request = frappe.get_doc({
		"doctype": "Material Request",
		"material_request_type": "Purchase",
		"company": sales_order.company,
		"transaction_date": frappe.utils.nowdate(),
		"schedule_date": sales_order.delivery_date,
	})
	for row in shortages:
		request.append("items", {
			"item_code": row["item_code"], "qty": row["qty"],
			"warehouse": warehouse, "schedule_date": sales_order.delivery_date,
			"sales_order": sales_order.name,
		})
	request.insert(ignore_permissions=True)
	return request


def _make_material_transfer(work_order, stores_warehouse):
	transfer = frappe.get_doc(make_stock_entry(work_order, "Material Transfer for Manufacture"))
	for row in transfer.items:
		row.s_warehouse = stores_warehouse
		row.allow_zero_valuation_rate = 0
	transfer.insert(ignore_permissions=True)
	return transfer


def _result(sales_order, work_order, material_transfer, material_request, already_started):
	bom_name = frappe.db.get_value("Work Order", work_order, "bom_no")
	bom_cost = frappe.utils.flt(frappe.db.get_value("BOM", bom_name, "total_cost"))
	estimate_name = get_estimate_for_sales_order(sales_order.name)
	estimate_cost = frappe.utils.flt(frappe.db.get_value("Print Estimate", estimate_name, "subtotal"))
	return {
		"work_order": work_order,
		"bom": bom_name,
		"material_transfer": material_transfer,
		"material_request": material_request,
		"already_started": already_started,
		"planned_bom_cost": bom_cost,
		"estimate_cost": estimate_cost,
		"cost_variance": bom_cost - estimate_cost,
		"work_order_status": frappe.db.get_value("Work Order", work_order, "docstatus"),
		"unvalued_items": _get_unvalued_items(
			frappe.get_doc("BOM", bom_name),
			f"Stores - {frappe.db.get_value('Company', sales_order.company, 'abbr')}",
		),
	}


def _require_permission(doctype, permission_type):
	"""Fail before privileged document creation if the caller could not
	perform the equivalent action through ERPNext itself."""
	if not frappe.has_permission(doctype, ptype=permission_type):
		frappe.throw(
			f"You need {permission_type} permission on {doctype} to start production.",
			frappe.PermissionError,
		)
