import frappe

# Paper rate now comes from a real Paper Type lookup (substrate + gsm),
# not a monkey-patched constant - this run proves the PERMANENT fix,
# not just the formula in isolation.


def run():
	# A press profile matching Mofeed's REAL raw math exactly (zero
	# gripper margin, zero make-ready sheets, 20% waste - his own
	# confirmed standard) - not our earlier arbitrary test press, which
	# had different placeholder values for unrelated testing.
	if not frappe.db.exists("Press Profile", "Golden Arrow Offset"):
		frappe.get_doc({
			"doctype": "Press Profile", "press_name": "Golden Arrow Offset",
			"machine_model": "Matches Mofeed's real math", "colour_heads": 4,
			"max_sheet_width_mm": 700, "max_sheet_height_mm": 1000,
			"gripper_margin_mm": 0, "makeready_cost": 0, "makeready_sheets": 0,
			"run_waste_pct": 20, "running_rate_per_1000": 0,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"product_type": "Folding Carton",
		"product_template": "Folding Carton",
		"finished_size_w": 510,   # 51cm flat blank, in mm to match our other estimates' units
		"finished_size_h": 450,
		"quantity": 1000,
		"colours_front": 3,
		"colours_back": 0,
		"printing_method": "Sheetwise",
		"ink_coverage": "Medium",
		"paper_type": "Ivory-350GSM",  # the dropdown pick - substrate/gsm auto-fill from this now
		"sheet_size": "700x1000",
		"press": "Golden Arrow Offset",
		"bleed_mm": 0, "gutter_mm": 0,  # Mofeed's 51x45 IS the full flat-blank
		# layout size already - our engine would otherwise add bleed+gutter
		# on top of it, double-counting a margin he's already accounted for.
		"die_width_cm": 53, "die_height_cm": 45,  # area now auto-computed
		"glue_sides": 1,
		"margin_pct": 10,
	})
	est.insert(ignore_permissions=True)
	print("STEP1_INSERTED (no template applied yet):", est.name)
	print("AUTO-FILLED substrate:", est.substrate, "| gsm:", est.gsm)

	# Now apply the template - the "choose a BOM" moment
	n_rows = est.apply_template()
	est.reload()
	print("STEP2_TEMPLATE_APPLIED, rows:", n_rows)
	for row in est.applied_cost_drivers:
		print("  ", row.cost_driver, "enabled=", row.enabled, "cost=", row.computed_cost)

	print("SHEETS_REQUIRED:", est.sheets_required)
	print("PAPER_COST:", est.paper_cost)
	print("DRIVER_COSTS_TOTAL:", est.driver_costs_total)
	print("SUBTOTAL:", est.subtotal)
	print("SELL_PRICE:", est.sell_price)

	expected_subtotal = 2055.25
	expected_sell = round(expected_subtotal * 1.10, 2)
	print("EXPECTED_SUBTOTAL:", expected_subtotal, "MATCH:", abs(est.subtotal - expected_subtotal) < 0.5)
	print("EXPECTED_SELL:", expected_sell, "MATCH:", abs(est.sell_price - expected_sell) < 0.5)

	frappe.db.commit()
