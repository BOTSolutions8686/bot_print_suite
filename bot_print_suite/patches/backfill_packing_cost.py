import frappe


def execute():
	"""Show existing Packing row overrides in the new simple form field."""
	rows = frappe.get_all(
		"Print Estimate Cost Driver Line",
		filters={"cost_override_enabled": 1},
		fields=["parent", "cost_driver", "cost_override"],
		order_by="parent asc, idx asc",
	)
	for row in rows:
		if "packing" not in (row.cost_driver or "").lower():
			continue
		frappe.db.set_value(
			"Print Estimate", row.parent,
			{
				"packing_cost_override_enabled": 1,
				"packing_cost": float(row.cost_override or 0),
			},
			update_modified=False,
		)
