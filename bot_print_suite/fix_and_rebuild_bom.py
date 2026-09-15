import frappe
from bot_print_suite.production.bom_bridge import create_job_bom

def run():
	est = frappe.get_doc("Print Estimate", "PE-Test Golden Arrow-00003")
	est.substrate = "SBS Board"
	est.gsm = 300
	est.save(ignore_permissions=True)
	print("FIXED_ESTIMATE: paper_cost=", est.paper_cost, "sheets=", est.sheets_required, "plates=", est.plates_count)

	# tear down the earlier bad BOM/item so we get a clean correct one
	old_bom = frappe.db.get_value("BOM", {"item": "JOB-GA-JOB-2026-0001"})
	if old_bom:
		frappe.get_doc("BOM", old_bom).cancel()
		frappe.delete_doc("BOM", old_bom, force=1, ignore_permissions=True)

	bom_name = create_job_bom("GA-JOB-2026-0001")
	bom = frappe.get_doc("BOM", bom_name)
	print("BOM_RECREATED:", bom.name, "DOCSTATUS:", bom.docstatus)
	for row in bom.items:
		print("  BOM_ITEM:", row.item_code, "QTY:", row.qty)

	frappe.db.commit()
