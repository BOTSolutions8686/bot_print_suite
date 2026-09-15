import frappe
from frappe.model.workflow import apply_workflow
from erpnext.selling.doctype.quotation.quotation import make_sales_order
from bot_print_suite.production.start_production import start_production


def run():
	# 1. Masters (idempotent - skip if already present)
	if not frappe.db.exists("Press Profile", "Heidelberg SM74"):
		frappe.get_doc({
			"doctype": "Press Profile", "press_name": "Heidelberg SM74",
			"machine_model": "Heidelberg Speedmaster 74", "colour_heads": 4,
			"max_sheet_width_mm": 740, "max_sheet_height_mm": 520,
			"gripper_margin_mm": 10, "makeready_cost": 500, "makeready_sheets": 50,
			"run_waste_pct": 2, "running_rate_per_1000": 250,
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("Sheet Size", "700x1000"):
		frappe.get_doc({"doctype": "Sheet Size", "sheet_size_name": "700x1000", "width_mm": 700, "height_mm": 1000}).insert(ignore_permissions=True)

	if not frappe.db.exists("Finishing Rate Card", {"operation": "Lamination"}):
		frappe.get_doc({
			"doctype": "Finishing Rate Card", "operation": "Lamination",
			"unit_basis": "Per 1000 Sheets", "rate": 120, "film_foil_type": "Gloss",
		}).insert(ignore_permissions=True)

	if not frappe.db.exists("Customer", "Golden Arrow Printing & Packaging Co."):
		frappe.get_doc({"doctype": "Customer", "customer_name": "Golden Arrow Printing & Packaging Co."}).insert(ignore_permissions=True)

	frappe.db.commit()
	print("STEP_1_MASTERS_OK")


	# 2. Enquiry -> Estimate
	enq = frappe.get_doc({
		"doctype": "Print Enquiry",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"contact_name": "Abdul Latif", "source": "Phone",
		"product_type": "Folding Carton",
		"rough_spec": "50,000 folding cartons, 4-colour, 300gsm board",
	})
	enq.insert(ignore_permissions=True)
	est_name = enq.make_print_estimate()

	est = frappe.get_doc("Print Estimate", est_name)
	est.finished_size_w = 90
	est.finished_size_h = 55
	est.quantity = 10000
	est.colours_front = 4
	est.colours_back = 0
	est.substrate = "SBS Board"
	est.gsm = 300
	est.sheet_size = "700x1000"
	est.press = "Heidelberg SM74"
	est.append("finishing_operations", {"finishing_rate_card": frappe.db.get_value("Finishing Rate Card", {"operation": "Lamination"})})
	est.save(ignore_permissions=True)
	frappe.db.commit()
	print("STEP_2_ENQUIRY_ESTIMATE_OK:", enq.name, est.name, "sell_price:", est.sell_price)

	# 3. Quotation + approval
	qtn_name = est.create_quotation()
	qtn = frappe.get_doc("Quotation", qtn_name)
	qtn = apply_workflow(qtn, "Submit for Approval")
	qtn = apply_workflow(qtn, "Approve")
	frappe.db.commit()
	print("STEP_3_QUOTATION_OK:", qtn.name, "docstatus:", qtn.docstatus, "state:", qtn.workflow_state)


	# 4. Job Order (via ERPNext's own quotation->SO flow)
	so = make_sales_order(qtn.name)
	so.delivery_date = frappe.utils.add_days(frappe.utils.nowdate(), 30)
	so.naming_series = "GA-JOB-.YYYY.-.####"
	so.insert(ignore_permissions=True)
	so.submit()
	frappe.db.commit()
	print("STEP_4_JOB_ORDER_OK:", so.name)

	# 5. Artwork approval (Draft -> Sent -> Approved)
	art = frappe.get_doc({"doctype": "Job Artwork", "sales_order": so.name, "version_no": 1})
	art.insert(ignore_permissions=True)
	art = apply_workflow(art, "Send to Customer")
	art = apply_workflow(art, "Approve")
	frappe.db.commit()
	print("STEP_5_ARTWORK_OK:", art.name, art.status)

	# 6. Start Production (BOM + routing + Work Order + material transfer draft)
	result = start_production(so.name)
	frappe.db.commit()
	print("STEP_6_PRODUCTION_OK:", result)

	so.reload()
	print("FINAL_JOB_STATUS:", so.custom_job_status)
	print("\n=== CHAIN COMPLETE ===")
	print("Enquiry:", enq.name, "| Estimate:", est.name, "| Quotation:", qtn.name)
	print("Job Order:", so.name, "| Work Order:", result["work_order"])
