"""
BOT Print Suite - Job Tracker strip (PLAN.md 4c).

The one sanctioned exception to "no custom UI": a shipment-tracking-style
pipeline showing where a job stands across the full chain. This module is
the DATA layer only - read-only, derived entirely from statuses that
already exist elsewhere (Quotation workflow_state, Job Artwork status,
Work Order/Delivery Note/Sales Invoice existence). No new state anywhere.
Rendering (Job Order form header, owner dashboard, later the portal) is a
thin client script consuming this API.
"""

import frappe
from bot_print_suite.production.bom_bridge import get_estimate_for_sales_order

STAGES = ["Enquiry", "Estimate", "Quote", "Approved", "Artwork", "Production", "Delivery", "Invoiced"]


@frappe.whitelist()
def count_jobs_due_this_week(filters=None):
	"""Number Card custom method - avoids the 'Today'/'Today+7' string-
	literal filter trap (plain frappe.get_list filters do NOT resolve
	those tokens; they get compared lexically against date strings and
	silently give wrong results - caught this via a real smoke test, not
	assumed safe). Real date math instead.
	`filters` is accepted (unused) because the Number Card widget's
	get_data() always calls this with a `filters` kwarg regardless of
	card type - omitting the parameter causes a silent TypeError on the
	client, which renders as a blank number instead of an error. Caught
	via an actual browser walkthrough, not assumed safe."""
	_require_sales_order_read()
	today = frappe.utils.nowdate()
	week_end = frappe.utils.add_days(today, 7)
	count = frappe.db.count("Sales Order", {
		"docstatus": 1, "delivery_date": ["between", [today, week_end]],
	})
	return {"value": count}


@frappe.whitelist()
def count_overdue_jobs(filters=None):
	_require_sales_order_read()
	today = frappe.utils.nowdate()
	count = frappe.db.count("Sales Order", {
		"docstatus": 1, "delivery_date": ["<", today],
		"custom_job_status": ["!=", "Delivered"],
	})
	return {"value": count}


@frappe.whitelist()
def get_job_tracker_data(sales_order):
	so = frappe.get_doc("Sales Order", sales_order)
	so.check_permission("read")

	so_item = frappe.db.get_value("Sales Order Item", {"parent": sales_order}, "prevdoc_docname")
	quotation_state = frappe.db.get_value("Quotation", so_item, "workflow_state") if so_item else None
	quotation_approved = quotation_state == "Approved"

	latest_artwork = frappe.get_all(
		"Job Artwork", filters={"sales_order": sales_order},
		fields=["status"], order_by="version_no desc", limit=1,
	)
	artwork_status = latest_artwork[0].status if latest_artwork else None
	artwork_approved = artwork_status == "Approved"

	has_submitted_wo = bool(frappe.db.exists("Work Order", {"sales_order": sales_order, "docstatus": 1}))
	has_submitted_dn = bool(frappe.db.exists(
		"Delivery Note Item", {"against_sales_order": sales_order, "docstatus": 1}))
	has_submitted_si = bool(frappe.db.exists(
		"Sales Invoice Item", {"sales_order": sales_order, "docstatus": 1}))

	completed = [True, True, True, quotation_approved, artwork_approved, has_submitted_dn, has_submitted_dn, has_submitted_si]

	if not quotation_approved:
		current_index, status_line = 3, "Awaiting approval"
	elif not artwork_approved:
		current_index = 4
		status_line = {
			None: "Artwork not uploaded", "Draft": "Artwork pending",
			"Sent to Customer": "Awaiting customer approval",
			"Revision Requested": "Revision requested",
		}.get(artwork_status, "Artwork pending")
	elif not has_submitted_wo:
		current_index, status_line = 5, "Ready for production"
	elif not has_submitted_dn:
		current_index = 5
		status_line = so.custom_job_status or "In production"
	elif not has_submitted_si:
		current_index, status_line = 6, "Out for delivery"
	else:
		current_index, status_line = 7, "Invoiced"

	return {
		"stages": STAGES,
		"completed": completed,
		"current_index": current_index,
		"status_line": status_line,
	}


def _require_sales_order_read():
	if not frappe.has_permission("Sales Order", ptype="read"):
		frappe.throw("You need read permission on Sales Order to view job metrics.", frappe.PermissionError)
