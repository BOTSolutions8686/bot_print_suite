import frappe


def run():
	est = frappe.get_doc("Print Estimate", "PE-Golden Arrow Printing & Packaging Co.-00038")

	# Test manual override on Artwork
	for row in est.applied_cost_drivers:
		if row.cost_driver == "Artwork":
			row.cost_override_enabled = 1
			row.cost_override = 999
	est.save(ignore_permissions=True)
	for row in est.applied_cost_drivers:
		if row.cost_driver == "Artwork":
			print("Artwork override test:", row.computed_cost, "source:", row.source, "(should be 999, Manual Override)")
			row.cost_override_enabled = 0  # clear it back
			row.cost_override = None

	# Test zero as a real override (the bug this session fixed - 0 must
	# not silently fall back to the calculated value)
	for row in est.applied_cost_drivers:
		if row.cost_driver == "Artwork":
			row.cost_override_enabled = 1
			row.cost_override = 0
	est.save(ignore_permissions=True)
	for row in est.applied_cost_drivers:
		if row.cost_driver == "Artwork":
			print("Artwork zero-override test:", row.computed_cost, "source:", row.source, "(should be 0, Manual Override)")
			row.cost_override_enabled = 0
			row.cost_override = None
	est.save(ignore_permissions=True)

	# Test sheets_required_override
	est.sheets_required_override = 5000
	est.save(ignore_permissions=True)
	print("Sheets override test:", est.sheets_required, "(should be 5000)")
	print("Paper cost recomputed:", est.paper_cost)

	# Clean up - restore to the real, correct state
	est.sheets_required_override = None
	est.save(ignore_permissions=True)
	print("Restored sheets_required:", est.sheets_required, "| Subtotal:", est.subtotal)
	frappe.db.commit()
