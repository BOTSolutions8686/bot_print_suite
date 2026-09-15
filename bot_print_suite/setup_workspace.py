import frappe
import json


def run():
	if frappe.db.exists("Workspace", "Print Suite"):
		print("WORKSPACE_EXISTS")
		return

	content_blocks = [
		{"id": "header1", "type": "header", "data": {"text": "<span class=\"h4\"><b>Print Suite</b></span>", "col": 12}},
		{"id": "card1", "type": "number_card", "data": {"number_card_name": "Open Enquiries", "col": 4}},
		{"id": "card2", "type": "number_card", "data": {"number_card_name": "Estimates Pending", "col": 4}},
		{"id": "card3", "type": "number_card", "data": {"number_card_name": "Quotes Awaiting Approval", "col": 4}},
		{"id": "card4", "type": "number_card", "data": {"number_card_name": "Jobs in Production", "col": 4}},
		{"id": "card5", "type": "number_card", "data": {"number_card_name": "Jobs Due This Week", "col": 4}},
		{"id": "card6", "type": "number_card", "data": {"number_card_name": "Overdue Jobs", "col": 4}},
		{"id": "chart1", "type": "chart", "data": {"chart_name": "Monthly Sales", "col": 6}},
		{"id": "chart2", "type": "chart", "data": {"chart_name": "Enquiry Source Breakdown", "col": 6}},
		{"id": "shortcuts_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Shortcuts</b></span>", "col": 12}},
		{"id": "sc1", "type": "shortcut", "data": {"shortcut_name": "New Enquiry", "col": 3}},
		{"id": "sc2", "type": "shortcut", "data": {"shortcut_name": "New Estimate", "col": 3}},
		{"id": "sc3", "type": "shortcut", "data": {"shortcut_name": "Job Board", "col": 3}},
	]

	doc = frappe.get_doc({
		"doctype": "Workspace",
		"name": "Print Suite",
		"title": "Print Suite",
		"label": "Print Suite",
		"module": "BOT Print Suite",
		"public": 1,
		"is_hidden": 0,
		"icon": "printing",
		"parent_page": "",
		"for_user": "",
		"indicator_color": "blue",
		"content": json.dumps(content_blocks),
		"number_cards": [
			{"number_card_name": n} for n in
			["Open Enquiries", "Estimates Pending", "Quotes Awaiting Approval",
			 "Jobs in Production", "Jobs Due This Week", "Overdue Jobs"]
		],
		"charts": [
			{"chart_name": n, "label": n} for n in ["Monthly Sales", "Enquiry Source Breakdown"]
		],
		"shortcuts": [
			{"type": "DocType", "link_to": "Print Enquiry", "label": "New Enquiry", "doc_view": "New"},
			{"type": "DocType", "link_to": "Print Estimate", "label": "New Estimate", "doc_view": "New"},
			{"type": "DocType", "link_to": "Sales Order", "label": "Job Board"},
		],
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	print("WORKSPACE_CREATED")
