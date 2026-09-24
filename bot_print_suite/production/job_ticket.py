import frappe
from frappe.utils import cint, flt


ARTWORK_STATUS_AR = {
	"Draft": "مسودة",
	"Sent to Customer": "مرسل للعميل",
	"Approved": "معتمد",
	"Revision Requested": "مطلوب تعديل",
}


def get_job_ticket_context(sales_order_name):
	"""Return production-only information for the bilingual Job Ticket."""
	order = frappe.get_doc("Sales Order", sales_order_name)
	quotation_name = next(
		(
			row.prevdoc_docname
			for row in order.items
			if row.prevdoc_docname and frappe.db.exists("Quotation", row.prevdoc_docname)
		),
		None,
	)
	quotation = frappe.get_doc("Quotation", quotation_name) if quotation_name else None
	estimate_name = quotation.custom_print_estimate if quotation else None
	estimate = frappe.get_doc("Print Estimate", estimate_name) if estimate_name else None

	artwork_rows = frappe.get_all(
		"Job Artwork",
		filters={"sales_order": order.name},
		fields=["name", "version_no", "status", "artwork_file", "customer_comment"],
		order_by="version_no desc",
		limit=1,
	)
	artwork = artwork_rows[0] if artwork_rows else frappe._dict({
		"version_no": None, "status": "Not uploaded", "artwork_file": None,
		"customer_comment": None,
	})
	artwork.status_ar = ARTWORK_STATUS_AR.get(artwork.status, "لم يتم الرفع")

	if not estimate:
		return frappe._dict({"quotation": quotation_name, "estimate": None, "artwork": artwork, "operations": []})

	operations = []
	def add_operation(arabic, english, detail=""):
		operations.append(frappe._dict({"arabic": arabic, "english": english, "detail": detail}))

	add_operation("تجهيز واعتماد التصميم", "Artwork and prepress", artwork.status)
	add_operation("إعداد الألواح", "Plate preparation", f"{cint(estimate.colours_front) + cint(estimate.colours_back)} colours")
	add_operation("الطباعة", "Printing", estimate.press or "")
	if estimate.lamination_required:
		add_operation("التغليف الحراري", "Lamination")
	if estimate.die_requirement:
		add_operation("القص بالقالب", "Die-cutting", estimate.die_requirement)
	if cint(estimate.glue_sides):
		add_operation("اللصق", "Gluing", f"{cint(estimate.glue_sides)} side(s)")
	if any(row.enabled and "pack" in (row.cost_driver or "").lower() for row in estimate.applied_cost_drivers):
		add_operation("التعبئة", "Packing")
	add_operation("فحص الجودة", "Quality control")

	return frappe._dict({
		"quotation": quotation_name,
		"estimate": estimate,
		"artwork": artwork,
		"operations": operations,
		"impressions": cint(estimate.sheets_required) * (2 if estimate.double_sided else 1),
		"colours": f"{cint(estimate.colours_front)} / {cint(estimate.colours_back)}",
		"sides": "وجهان / Both sides" if estimate.double_sided else "وجه واحد / One side",
		"die_size": (
			f"{flt(estimate.die_width_cm):g} x {flt(estimate.die_height_cm):g} cm"
			if estimate.die_width_cm and estimate.die_height_cm
			else "مساحة الورقة كاملة / Full sheet area"
		),
	})
