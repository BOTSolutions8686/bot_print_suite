import frappe

def run():
	ws = frappe.get_doc("Workspace", "Print Suite")
	ws.icon = "printing"
	ws.parent_page = ""
	ws.for_user = ""
	ws.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()
	print("FIXED:", ws.icon, "|", repr(ws.parent_page), "|", repr(ws.for_user))
