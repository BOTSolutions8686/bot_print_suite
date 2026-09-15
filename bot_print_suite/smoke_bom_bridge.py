import frappe
from bot_print_suite.production.bom_bridge import get_estimate_for_sales_order, create_job_bom


def run():
	so_name = "GA-JOB-2026-0001"

	est_name = get_estimate_for_sales_order(so_name)
	print("LINKED_ESTIMATE:", est_name)

	# re-save to compute plates_count (added to the doctype after this
	# estimate was first saved, so the field is currently empty)
	est = frappe.get_doc("Print Estimate", est_name)
	est.save(ignore_permissions=True)
	print("SHEETS_REQUIRED:", est.sheets_required, "PLATES_COUNT:", est.plates_count)

	bom_name = create_job_bom(so_name)
	bom = frappe.get_doc("BOM", bom_name)
	print("BOM_CREATED:", bom.name, "DOCSTATUS:", bom.docstatus, "ITEM:", bom.item)
	for row in bom.items:
		print("  BOM_ITEM:", row.item_code, "QTY:", row.qty)

	so = frappe.get_doc("Sales Order", so_name)
	print("JOB_STATUS_AFTER_BOM:", so.custom_job_status)

	frappe.db.commit()
