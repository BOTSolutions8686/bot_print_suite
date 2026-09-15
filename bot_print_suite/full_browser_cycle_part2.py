import frappe
from frappe.model.workflow import apply_workflow
from erpnext.selling.doctype.quotation.quotation import make_sales_order

EST_NAME = "PE-Golden Arrow Printing & Packaging Co.-00004"


def run():
	est = frappe.get_doc("Print Estimate", EST_NAME)

	# 3. Quotation + approval workflow
	qtn_name = est.create_quotation()
	qtn = frappe.get_doc("Quotation", qtn_name)
	qtn = apply_workflow(qtn, "Submit for Approval")
	qtn = apply_workflow(qtn, "Approve")
	print("STEP3_QUOTATION:", qtn.name, "state:", qtn.workflow_state, "docstatus:", qtn.docstatus)

	# 4. Job Order via ERPNext's own Quotation -> Sales Order flow
	so = make_sales_order(qtn.name)
	so.delivery_date = frappe.utils.add_days(frappe.utils.nowdate(), 14)
	so.naming_series = "GA-JOB-.YYYY.-.####"
	so.insert(ignore_permissions=True)
	so.submit()
	print("STEP4_JOB_ORDER:", so.name)

	frappe.db.commit()
