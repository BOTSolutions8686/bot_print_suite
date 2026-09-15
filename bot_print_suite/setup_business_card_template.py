import frappe


def run():
	if frappe.db.exists("Product Estimation Template", "Business Card"):
		print("Already exists")
		return

	# Standard business cards are usually just guillotine-cut (no die),
	# and never glued - both included but OFF by default, since a
	# custom-shaped card (rounded corners, cut-out logo) is the
	# exception, not the rule. This matches what real research into
	# print-industry cost structures confirmed: die-cutting is
	# near-universal for cartons, but only situational for cards.
	template = frappe.get_doc({
		"doctype": "Product Estimation Template",
		"template_name": "Business Card",
		"product_type": "Commercial",
		"notes": "Standard business cards: no die (guillotine cut), no "
			"glue. Both included as OPTIONAL, off by default, for the "
			"less common custom-shaped card. Not yet calibrated against "
			"a real Golden Arrow card job - built from what we know "
			"generalizes from the carton job, not independently confirmed.",
		"drivers": [
			{"cost_driver": "Plate", "required": 1, "default_enabled": 1},
			{"cost_driver": "Printing", "required": 1, "default_enabled": 1},
			{"cost_driver": "Cutting", "required": 1, "default_enabled": 1},
			{"cost_driver": "Artwork", "required": 0, "default_enabled": 1},
			{"cost_driver": "Packing", "required": 0, "default_enabled": 1},
			{"cost_driver": "Die / Frame", "required": 0, "default_enabled": 0},
			{"cost_driver": "Glue - 1 Side", "required": 0, "default_enabled": 0},
		],
	})
	template.insert(ignore_permissions=True)
	print("Created: Business Card template,", len(template.drivers), "drivers")
	frappe.db.commit()
