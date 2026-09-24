"""
BOT Print Suite - "Start Production" one-click action (PLAN.md 4d).

Chains: ensure BOM exists (via bom_bridge) -> create + submit Work Order
(this is where block_production_without_approved_artwork actually fires
for real, not just in a smoke test) -> pre-fill a draft Material Transfer
Stock Entry for the user to review and submit themselves (deliberately
left as a draft - actually moving stock is a real inventory event and
stays a human action, consistent with the design principle in PLAN.md 4d:
"the app GENERATES standard ERPNext documents, it never replaces them").
"""

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
from bot_print_suite.production.bom_bridge import create_job_bom


@frappe.whitelist()
def start_production(sales_order_name):
	so = frappe.get_doc("Sales Order", sales_order_name)
	so.check_permission("write")
	_require_permission("BOM", "create")
	_require_permission("Work Order", "create")
	_require_permission("Work Order", "submit")
	_require_permission("Stock Entry", "create")

	existing_work_order = frappe.db.get_value(
		"Work Order",
		{"sales_order": sales_order_name, "docstatus": ["<", 2]},
		"name",
	)
	if existing_work_order:
		material_transfer = frappe.db.get_value(
			"Stock Entry",
			{
				"work_order": existing_work_order,
				"stock_entry_type": "Material Transfer for Manufacture",
				"docstatus": ["<", 2],
			},
			"name",
		)
		return {
			"work_order": existing_work_order,
			"material_transfer": material_transfer,
			"already_started": True,
		}

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
	work_order.submit()

	frappe.db.set_value("Sales Order", so.name, "custom_job_status", "Plates")

	material_transfer = frappe.get_doc(make_stock_entry(work_order.name, "Material Transfer for Manufacture"))
	stores_warehouse = f"Stores - {abbr}"
	for row in material_transfer.items:
		row.s_warehouse = stores_warehouse
		# No purchase history exists for these items yet (procurement is
		# stock ERPNext, configured - not something this bridge builds).
		# Zero valuation is the honest state, not a workaround: it doesn't
		# touch our costing, which comes entirely from the estimation
		# engine, independent of ERPNext's stock valuation.
		row.allow_zero_valuation_rate = 1
	material_transfer.insert(ignore_permissions=True)  # left as draft - human submits

	return {
		"work_order": work_order.name,
		"material_transfer": material_transfer.name,
		"already_started": False,
	}


def _require_permission(doctype, permission_type):
	"""Fail before privileged document creation if the caller could not
	perform the equivalent action through ERPNext itself."""
	if not frappe.has_permission(doctype, ptype=permission_type):
		frappe.throw(
			f"You need {permission_type} permission on {doctype} to start production.",
			frappe.PermissionError,
		)
