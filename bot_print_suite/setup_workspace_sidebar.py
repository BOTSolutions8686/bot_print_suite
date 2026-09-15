import frappe

def run():
	# 1. Workspace Sidebar - the left navigation tree shown when browsing
	#    the workspace. Separate v16 concept from the Workspace record
	#    itself (which only holds the dashboard content).
	if not frappe.db.exists("Workspace Sidebar", "Print Suite"):
		ws_sidebar = frappe.get_doc({
			"doctype": "Workspace Sidebar",
			"title": "Print Suite",
			"module": "BOT Print Suite",
			"app": "bot_print_suite",
			"header_icon": "printing",
			"items": [
				{"type": "Link", "label": "Print Suite", "link_type": "Workspace", "link_to": "Print Suite", "icon": "dashboard"},
				{"type": "Section Break", "label": "Sales"},
				{"type": "Link", "label": "Print Enquiry", "link_type": "DocType", "link_to": "Print Enquiry"},
				{"type": "Link", "label": "Print Estimate", "link_type": "DocType", "link_to": "Print Estimate"},
				{"type": "Link", "label": "Quotation", "link_type": "DocType", "link_to": "Quotation"},
				{"type": "Section Break", "label": "Production"},
				{"type": "Link", "label": "Job Orders", "link_type": "DocType", "link_to": "Sales Order"},
				{"type": "Link", "label": "Job Artwork", "link_type": "DocType", "link_to": "Job Artwork"},
				{"type": "Link", "label": "Work Order", "link_type": "DocType", "link_to": "Work Order"},
				{"type": "Section Break", "label": "Masters"},
				{"type": "Link", "label": "Press Profile", "link_type": "DocType", "link_to": "Press Profile"},
				{"type": "Link", "label": "Sheet Size", "link_type": "DocType", "link_to": "Sheet Size"},
				{"type": "Link", "label": "Finishing Rate Card", "link_type": "DocType", "link_to": "Finishing Rate Card"},
				{"type": "Section Break", "label": "Reports"},
				{"type": "Link", "label": "Estimated vs Actual", "link_type": "Report", "link_to": "Estimated vs Actual"},
			],
		})
		ws_sidebar.insert(ignore_permissions=True)
		print("WORKSPACE_SIDEBAR_CREATED")
	else:
		print("WORKSPACE_SIDEBAR_EXISTS")

	frappe.db.commit()
