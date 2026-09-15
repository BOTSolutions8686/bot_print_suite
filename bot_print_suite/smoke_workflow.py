import frappe
from frappe.model.workflow import apply_workflow


def run():
	est = frappe.get_doc("Print Estimate", "PE-Test Golden Arrow-00003")
	qtn_name = est.create_quotation()
	qtn = frappe.get_doc("Quotation", qtn_name)

	print("INITIAL_STATE:", qtn.workflow_state, "DOCSTATUS:", qtn.docstatus)

	qtn = apply_workflow(qtn, "Submit for Approval")
	print("AFTER_SUBMIT_FOR_APPROVAL:", qtn.workflow_state, "DOCSTATUS:", qtn.docstatus)

	qtn = apply_workflow(qtn, "Approve")
	print("AFTER_APPROVE:", qtn.workflow_state, "DOCSTATUS:", qtn.docstatus)

	qtn.reload()
	print("RELOADED_STATE:", qtn.workflow_state, "DOCSTATUS:", qtn.docstatus)

	# also exercise the reject -> revise loop on a second quotation
	qtn2_name = est.create_quotation()
	qtn2 = frappe.get_doc("Quotation", qtn2_name)
	qtn2 = apply_workflow(qtn2, "Submit for Approval")
	qtn2 = apply_workflow(qtn2, "Reject")
	print("AFTER_REJECT:", qtn2.workflow_state, "DOCSTATUS:", qtn2.docstatus)
	qtn2 = apply_workflow(qtn2, "Revise")
	print("AFTER_REVISE:", qtn2.workflow_state, "DOCSTATUS:", qtn2.docstatus)

	frappe.db.commit()
