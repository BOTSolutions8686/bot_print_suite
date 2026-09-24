import frappe


def execute():
	"""The bundled Sales Order helper replaces this duplicate Client Script."""
	if frappe.db.exists("Client Script", "Job Order Actions"):
		frappe.db.set_value("Client Script", "Job Order Actions", "enabled", 0)
