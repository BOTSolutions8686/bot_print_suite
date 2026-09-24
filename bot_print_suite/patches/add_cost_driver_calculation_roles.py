import frappe


ROLE_BY_DRIVER = {
	"Printing": "Printing",
	"Cutting": "Cutting",
	"Die / Frame": "Die",
	"Glue - 1 Side": "Glue",
	"Lamination": "Lamination",
	"Packing": "Packing",
}


def execute():
	"""Migrate known masters once; runtime behavior no longer depends on names."""
	for driver_name, role in ROLE_BY_DRIVER.items():
		if frappe.db.exists("Cost Driver", driver_name):
			frappe.db.set_value(
				"Cost Driver", driver_name, "calculation_role", role,
				update_modified=False,
			)

	# Persist the role on existing estimate rows so the browser can sync its
	# simple controls without extra requests or assumptions about item names.
	for row in frappe.get_all(
		"Print Estimate Cost Driver Line",
		fields=["name", "cost_driver"],
	):
		role = frappe.db.get_value("Cost Driver", row.cost_driver, "calculation_role")
		frappe.db.set_value(
			"Print Estimate Cost Driver Line", row.name, "calculation_role", role,
			update_modified=False,
		)
