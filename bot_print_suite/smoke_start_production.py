import frappe
from bot_print_suite.production.start_production import start_production


def run():
	old_bom = frappe.db.get_value("BOM", {"item": "JOB-GA-JOB-2026-0001", "docstatus": 1})
	if old_bom:
		doc = frappe.get_doc("BOM", old_bom)
		doc.cancel()
		frappe.delete_doc("BOM", old_bom, force=1, ignore_permissions=True)
		frappe.db.commit()
		print("OLD_BOM_CLEARED")

	result = start_production("GA-JOB-2026-0001")
	print("START_PRODUCTION_RESULT:", result)

	wo = frappe.get_doc("Work Order", result["work_order"])
	print("WORK_ORDER:", wo.name, "DOCSTATUS:", wo.docstatus, "QTY:", wo.qty)

	bom = frappe.get_doc("BOM", wo.bom_no)
	print("BOM_OPERATIONS:")
	for op in bom.operations:
		print("  ", op.operation, "|", op.workstation, "| rate:", op.hour_rate)

	mt = frappe.get_doc("Stock Entry", result["material_transfer"])
	print("MATERIAL_TRANSFER:", mt.name, "DOCSTATUS:", mt.docstatus, "PURPOSE:", mt.purpose)

	so = frappe.get_doc("Sales Order", "GA-JOB-2026-0001")
	print("JOB_STATUS:", so.custom_job_status)

	frappe.db.commit()
