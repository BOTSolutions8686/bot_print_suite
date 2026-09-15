import frappe


def run():
	glue = frappe.get_doc("Cost Driver", "Glue - 1 Side")
	glue.measurement_basis = "Per Side"
	glue.notes += " UPDATED: converted from Flat Fee to Per Side (150 SAR/side) " \
		"so the cost genuinely scales with Glue - Number of Sides on the estimate, " \
		"per Mofeed's own note that price changes based on side count. The " \
		"per-side rate itself (150) is an INFERENCE from his one confirmed " \
		"1-side number, not independently confirmed for 2+ sides - worth " \
		"checking with him directly if a real 2-side job comes up."
	glue.save(ignore_permissions=True)
	print("Updated Glue driver: measurement_basis =", glue.measurement_basis, "rate =", glue.rate)
	frappe.db.commit()
