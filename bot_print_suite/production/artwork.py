import frappe
from frappe import _


QUOTATION_ARTWORK_FIELD = "custom_customer_artwork"


def _source_quotation(sales_order):
	return next(
		(
			row.prevdoc_docname
			for row in sales_order.items
			if row.prevdoc_docname
			and frappe.db.exists("Quotation", row.prevdoc_docname)
		),
		None,
	)


def _quotation_artwork(quotation):
	if not quotation:
		return None
	return frappe.db.get_value(
		"File",
		{
			"attached_to_doctype": "Quotation",
			"attached_to_name": quotation,
			"attached_to_field": QUOTATION_ARTWORK_FIELD,
		},
		"file_url",
		order_by="creation desc",
	)


@frappe.whitelist()
def get_or_create_job_artwork(sales_order_name):
	"""Open the job's artwork record, carrying quotation artwork into version 1."""
	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	sales_order.check_permission("read")
	if sales_order.docstatus != 1:
		frappe.throw(_("Submit the Sales Order before starting artwork review."))

	existing = frappe.get_all(
		"Job Artwork",
		filters={"sales_order": sales_order.name},
		fields=["name"],
		order_by="version_no desc",
		limit=1,
	)
	if existing:
		return existing[0].name

	if not frappe.has_permission("Job Artwork", "create"):
		frappe.throw(_("You do not have permission to create Job Artwork."), frappe.PermissionError)

	artwork = frappe.get_doc({
		"doctype": "Job Artwork",
		"sales_order": sales_order.name,
		"version_no": 1,
		"artwork_file": _quotation_artwork(_source_quotation(sales_order)),
	}).insert()
	return artwork.name
