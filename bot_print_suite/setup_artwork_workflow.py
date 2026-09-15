import frappe


def run():
	for state in ["Draft", "Sent to Customer", "Approved", "Revision Requested"]:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(ignore_permissions=True)

	for action in ["Send to Customer", "Approve", "Request Revision"]:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)

	if frappe.db.exists("Workflow", "Artwork Approval"):
		print("WORKFLOW_EXISTS")
		frappe.db.commit()
		return

	wf = frappe.get_doc({
		"doctype": "Workflow",
		"workflow_name": "Artwork Approval",
		"document_type": "Job Artwork",
		"is_active": 1,
		"send_email_alert": 0,
		"workflow_state_field": "status",
		"states": [
			{"state": "Draft", "doc_status": "0", "allow_edit": "Sales User"},
			{"state": "Sent to Customer", "doc_status": "0", "allow_edit": "Sales Manager"},
			{"state": "Approved", "doc_status": "0", "allow_edit": "Sales Manager"},
			{"state": "Revision Requested", "doc_status": "0", "allow_edit": "Sales Manager"},
		],
		"transitions": [
			{"state": "Draft", "action": "Send to Customer", "next_state": "Sent to Customer", "allowed": "Sales User"},
			{"state": "Sent to Customer", "action": "Approve", "next_state": "Approved", "allowed": "Sales Manager"},
			{"state": "Sent to Customer", "action": "Request Revision", "next_state": "Revision Requested", "allowed": "Sales Manager"},
		],
	})
	wf.insert(ignore_permissions=True)
	frappe.db.commit()
	print("WORKFLOW_CREATED")
