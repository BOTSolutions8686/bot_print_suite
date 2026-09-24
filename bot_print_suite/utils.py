import frappe


def set_print_job_naming_series(doc, method=None):
	"""Use a recognisable job number for Sales Orders made by Print Suite."""
	if doc.get("custom_print_estimate") and doc.get("naming_series") == "SAL-ORD-.YYYY.-":
		doc.naming_series = "GA-JOB-.YYYY.-.####"


def assign_job_item_to_quotation(doc, method=None):
	"""Give an app-generated Quotation its permanent finished-good Item
	before ERPNext maps it into a Sales Order.

	The Quotation remains customer-friendly while it is a draft, using the
	generic service placeholder. On submission its unique stock Item is set
	on the still-editable Quotation rows, so the native Quotation -> Sales
	Order mapper carries the correct production Item forward without any
	after-submit database edits.
	"""
	if not doc.get("custom_print_estimate"):
		return

	est = frappe.get_doc("Print Estimate", doc.custom_print_estimate)
	item_code = _get_or_create_quotation_job_item(doc.name, est)
	for row in doc.items:
		if (row.item_code or "").startswith("PRINT-JOB-"):
			row.item_code = item_code
			row.item_name = frappe.db.get_value("Item", item_code, "item_name")


def _get_or_create_quotation_job_item(quotation_name, est):
	code = f"JOB-{quotation_name}"
	if frappe.db.exists("Item", code):
		return code

	from bot_print_suite.production.bom_bridge import _ensure_item_group

	frappe.get_doc({
		"doctype": "Item",
		"item_code": code,
		"item_name": f"{est.product_type} - {quotation_name}",
		"item_group": _ensure_item_group("Finished Job"),
		"stock_uom": "Nos",
		"is_stock_item": 1,
	}).insert(ignore_permissions=True)
	return code


def set_print_job_delivery_warehouse(doc, method=None):
	"""Keep print-job deliveries simple and safe.

	ERPNext may carry the company's raw-material default warehouse onto a
	Delivery Note created from a Sales Order.  Finished print jobs must leave
	from Finished Goods instead.  Only our job-specific Items are changed, so
	ordinary ERPNext deliveries retain their native behaviour.
	"""
	if not doc.get("company"):
		return

	abbr = frappe.db.get_value("Company", doc.company, "abbr")
	warehouse = f"Finished Goods - {abbr}" if abbr else None
	if not warehouse or not frappe.db.exists("Warehouse", warehouse):
		return

	for row in doc.items:
		if (row.item_code or "").startswith("JOB-"):
			row.warehouse = warehouse

_QUOTATION_STATUS_TO_ENQUIRY_STATUS = {
	"Ordered": "Won",
	"Lost": "Lost",
}


def sync_enquiry_status_from_quotation(doc, method=None):
	"""doc_event on Quotation.on_update - small status-sync hook, not a
	status engine (PLAN.md section 1: 'Small doc_events, not a status
	engine'). Only acts when the Quotation traces back to one of our
	estimates and its status just landed on Ordered/Lost."""
	new_status = _QUOTATION_STATUS_TO_ENQUIRY_STATUS.get(doc.status)
	if not new_status:
		return
	estimate_ref = doc.get("custom_print_estimate")
	if not estimate_ref:
		return
	enquiry = frappe.db.get_value("Print Estimate", estimate_ref, "enquiry")
	if enquiry:
		frappe.db.set_value("Print Enquiry", enquiry, "status", new_status)


_JOB_STAGES = {"Prepress", "Plates", "Printing", "Finishing", "QC", "Delivered"}


def block_production_without_approved_artwork(doc, method=None):
	"""validate hook on Work Order - PLAN.md 4b: 'a validate hook on Work
	Order prevents creation/submission while the Sales Order's latest Job
	Artwork status != Approved.' The one piece of real enforcement logic
	in the whole Job Order section - everything else there is fields and
	workflow states."""
	if not doc.sales_order:
		return
	latest = frappe.get_all(
		"Job Artwork",
		filters={"sales_order": doc.sales_order},
		fields=["status"],
		order_by="version_no desc",
		limit=1,
	)
	if not latest or latest[0].status != "Approved":
		frappe.throw(
			f"Cannot start production for {doc.sales_order}: artwork is not "
			f"yet Approved (current: {latest[0].status if latest else 'no artwork uploaded'})."
		)


def set_print_job_operating_cost_account(doc, method=None):
	"""Put print-job manufacture overhead into finished-goods valuation."""
	if (doc.get("purpose") != "Manufacture" and doc.get("stock_entry_type") != "Manufacture") or not doc.get("work_order"):
		return
	work_order = frappe.db.get_value("Work Order", doc.work_order, ["sales_order", "company"], as_dict=True)
	if not work_order or not work_order.sales_order:
		return
	from bot_print_suite.production.bom_bridge import get_estimate_for_sales_order
	if not get_estimate_for_sales_order(work_order.sales_order):
		return
	account = frappe.db.get_value("Account", {
		"company": work_order.company,
		"account_type": "Expenses Included In Valuation",
		"is_group": 0,
	}, "name")
	if not account:
		frappe.throw(
			f"Create an Expenses Included In Valuation account for {work_order.company} before completing production."
		)
	for row in doc.get("additional_costs") or []:
		if not row.expense_account:
			row.expense_account = account


def sync_job_status_from_job_card(doc, method=None):
	"""on_update hook on Job Card - PLAN.md 4: rollup job_status across
	Job Cards onto the Sales Order. Light rollup, not a state machine:
	if the Job Card's operation name matches one of our canonical stages,
	push it onto the linked Sales Order's custom_job_status. Operation
	naming convention is established properly in step 7 (4d, routing
	derived from the estimate) - this just wires the update mechanism."""
	if doc.operation not in _JOB_STAGES:
		return
	if not doc.work_order:
		return
	sales_order = frappe.db.get_value("Work Order", doc.work_order, "sales_order")
	if sales_order:
		frappe.db.set_value("Sales Order", sales_order, "custom_job_status", doc.operation)
