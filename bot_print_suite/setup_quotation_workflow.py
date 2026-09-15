import frappe


def run():
	for state in ["Draft", "Pending Approval", "Approved", "Rejected"]:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(ignore_permissions=True)

	for action in ["Submit for Approval", "Approve", "Reject", "Revise"]:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)

	if frappe.db.exists("Workflow", "Quotation Approval"):
		print("WORKFLOW_EXISTS")
		frappe.db.commit()
		return


	wf = frappe.get_doc({
		"doctype": "Workflow",
		"workflow_name": "Quotation Approval",
		"document_type": "Quotation",
		"is_active": 1,
		"send_email_alert": 0,
		"workflow_state_field": "workflow_state",
		"states": [
			{"state": "Draft", "doc_status": "0", "allow_edit": "Sales User"},
			{"state": "Pending Approval", "doc_status": "0", "allow_edit": "Sales Manager"},
			{"state": "Approved", "doc_status": "1", "allow_edit": "Sales Manager"},
			{"state": "Rejected", "doc_status": "0", "allow_edit": "Sales User"},
		],
		"transitions": [
			{"state": "Draft", "action": "Submit for Approval", "next_state": "Pending Approval", "allowed": "Sales User"},
			{"state": "Pending Approval", "action": "Approve", "next_state": "Approved", "allowed": "Sales Manager"},
			{"state": "Pending Approval", "action": "Reject", "next_state": "Rejected", "allowed": "Sales Manager"},
			{"state": "Rejected", "action": "Revise", "next_state": "Draft", "allowed": "Sales User"},
		],
	})
	wf.insert(ignore_permissions=True)
	frappe.db.commit()
	print("WORKFLOW_CREATED")
