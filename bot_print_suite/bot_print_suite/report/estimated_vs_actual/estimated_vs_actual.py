"""
BOT Print Suite - Estimated vs Actual report (PLAN.md section 4b).

Deliberately simple per the plan: "One Frappe Query Report. No dashboard
engineering in Phase 1." One script report, no custom pages. Shows, per
Job Order: what we estimated it would cost/sell for, what it actually
cost (materials consumed + operating cost from linked Work Orders), and
what was actually invoiced - the report the whole technical proposal's
"estimated vs actual margin" promise depends on.
"""

import frappe
from bot_print_suite.production.bom_bridge import get_estimate_for_sales_order


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data


def get_columns():
	return [
		{"label": "Job Order", "fieldname": "sales_order", "fieldtype": "Link",
		 "options": "Sales Order", "width": 160},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 160},
		{"label": "Estimated Cost", "fieldname": "estimated_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Estimated Sell", "fieldname": "estimated_sell", "fieldtype": "Currency", "width": 130},
		{"label": "Actual Cost", "fieldname": "actual_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Invoiced Amount", "fieldname": "invoiced_amount", "fieldtype": "Currency", "width": 130},
		{"label": "Estimated Margin %", "fieldname": "estimated_margin_pct", "fieldtype": "Percent", "width": 140},
		{"label": "Actual Margin %", "fieldname": "actual_margin_pct", "fieldtype": "Percent", "width": 140},
	]


def get_data(filters):
	sales_orders = frappe.get_all(
		"Sales Order",
		filters={"docstatus": 1},
		fields=["name", "customer"],
	)

	rows = []
	for so in sales_orders:
		est_name = get_estimate_for_sales_order(so.name)
		if not est_name:
			continue  # not a print job order (no linked estimate) - skip

		est = frappe.db.get_value(
			"Print Estimate", est_name, ["subtotal", "sell_price"], as_dict=True
		)
		if not est:
			continue

		actual_cost = _get_actual_cost(so.name)
		invoiced_amount = _get_invoiced_amount(so.name)

		estimated_margin_pct = (
			(est.sell_price - est.subtotal) / est.sell_price * 100
			if est.sell_price else 0
		)
		actual_margin_pct = (
			(invoiced_amount - actual_cost) / invoiced_amount * 100
			if invoiced_amount else 0
		)

		rows.append({
			"sales_order": so.name,
			"customer": so.customer,
			"estimated_cost": est.subtotal,
			"estimated_sell": est.sell_price,
			"actual_cost": actual_cost,
			"invoiced_amount": invoiced_amount,
			"estimated_margin_pct": round(estimated_margin_pct, 2),
			"actual_margin_pct": round(actual_margin_pct, 2),
		})

	return rows


def _get_actual_cost(sales_order):
	work_orders = frappe.get_all(
		"Work Order", filters={"sales_order": sales_order}, fields=["name", "actual_operating_cost"]
	)
	if not work_orders:
		return 0

	operating_cost = sum(wo.actual_operating_cost or 0 for wo in work_orders)

	material_cost = 0
	for wo in work_orders:
		entries = frappe.get_all(
			"Stock Entry",
			filters={"work_order": wo.name, "purpose": "Manufacture", "docstatus": 1},
			fields=["total_outgoing_value"],
		)
		material_cost += sum(e.total_outgoing_value or 0 for e in entries)

	return operating_cost + material_cost


def _get_invoiced_amount(sales_order):
	rows = frappe.get_all(
		"Sales Invoice Item",
		filters={"sales_order": sales_order, "docstatus": 1},
		fields=["amount"],
	)
	return sum(r.amount or 0 for r in rows)
