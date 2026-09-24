import frappe


def execute():
	"""Preserve manual Packing values on sites that ran the older backfill."""
	packing_drivers = frappe.get_all(
		"Cost Driver", filters={"calculation_role": "Packing"}, pluck="name"
	)
	if not packing_drivers:
		return

	for row in frappe.get_all(
		"Print Estimate Cost Driver Line",
		filters={"cost_driver": ["in", packing_drivers], "cost_override_enabled": 1},
		fields=["parent", "cost_override"],
		order_by="parent asc, idx asc",
	):
		frappe.db.set_value(
			"Print Estimate", row.parent,
			{
				"packing_cost_override_enabled": 1,
				"packing_cost": float(row.cost_override or 0),
			},
			update_modified=False,
		)
