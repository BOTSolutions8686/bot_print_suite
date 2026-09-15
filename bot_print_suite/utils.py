import frappe

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
