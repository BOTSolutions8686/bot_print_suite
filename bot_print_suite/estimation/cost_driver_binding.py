"""
BOT Print Suite - binds the generic Cost Driver engine to a real
Print Estimate document (PLAN.md Step 10 - live form integration).

Mirrors estimation/engine.py's own split: the pure math lives in
cost_driver_engine.py (frappe-free, golden-tested against Mofeed's real
numbers). This module is the ONLY place that touches frappe.*/the DB to
connect that pure engine to an actual estimate.
"""

import frappe
from bot_print_suite.estimation.cost_driver_engine import compute_cost_driver, compute_cartons

# Driver names whose cost is zeroed when reusing an existing die -
# matches Golden Arrow's own confirmed rule: repeat customers don't pay
# for the die again. Matched by substring so "Die / Frame" and any future
# die-like driver name still gets caught without needing an exact name.
_DIE_LIKE_KEYWORDS = ("die", "frame", "قالب")

# Cutting is confirmed real physics too (Talha, 2026-08-19): one cutting
# pass on a stack of press SHEETS produces `ups` finished pieces at once,
# so the tiered "Per 1000 Pieces" cost (still keyed by piece quantity,
# per Mofeed's own real data points) needs to be divided by Ups per
# Sheet to land on the real per-job cutting cost - a 500,000-piece job
# at 4 ups is really only cutting 125,000 sheets' worth of stacks, not
# 500,000 individual pieces. Matched by substring, same convention as
# _DIE_LIKE_KEYWORDS, so "Cutting" and any future cutting-like driver
# name still gets caught without an exact-name dependency.
_CUTTING_LIKE_KEYWORDS = ("cutting",)

# Real gap found and fixed (Talha, 2026-08-19): the tiered "Per 1000
# Sheets" Printing driver was blind to single vs double-sided printing -
# a sheet printed on both sides needs two passes through the press, so
# the effective sheet-equivalent volume doubles. This is genuinely
# independent of Colours Back (a job can reuse the same 4 plates on
# both sides via Work and Turn while still needing double the press
# time), so it's driven by doc.double_sided, not colours. Doubling
# happens BEFORE the tier lookup, not just on the final cost - since
# it's a declining-rate table, doubled volume can land in a cheaper
# tier bracket entirely, not just double the same rate.
_PRINTING_LIKE_KEYWORDS = ("printing",)


def apply_template(doc):
	"""Populates applied_cost_drivers from doc.product_template's driver
	list - the 'choose a BOM' moment. Only called explicitly (via the
	whitelisted method), never automatically in validate(), so picking a
	template doesn't silently wipe out rows an estimator already
	hand-edited for this specific job."""
	if not doc.product_template:
		return
	template = frappe.get_doc("Product Estimation Template", doc.product_template)
	doc.applied_cost_drivers = []
	for line in template.drivers:
		doc.append("applied_cost_drivers", {
			"cost_driver": line.cost_driver,
			"enabled": 1 if line.default_enabled else 0,
		})


def compute_driver_costs(doc):
	"""Computes computed_cost for every enabled row in
	applied_cost_drivers, and driver_costs_total as their sum. Pure
	arithmetic lives in cost_driver_engine.compute_cost_driver() - this
	function's only job is fetching each row's Cost Driver master and
	assembling the right job_values from the estimate's own fields."""
	if not doc.get("applied_cost_drivers"):
		doc.driver_costs_total = 0
		return

	# Explicit int()/float() casts - same bug class as engine.py and
	# print_estimate.py's validate(): field DEFAULT values (as opposed to
	# what a user actually typed) can arrive as strings from a fresh,
	# never-saved form (e.g. glue_sides default "0"), and this dict feeds
	# straight into arithmetic in compute_cost_driver(). Not yet hit in
	# practice (none of our real Cost Drivers use "Per Side" today), but
	# real enough to fix now rather than wait for it to surface later.
	# Cartons only needed for Packing's "Per Carton" basis, but it's
	# cheap to compute unconditionally and share via job_values like
	# everything else - avoids a second per-row DB fetch of Sheet Size.
	sheet = frappe.get_cached_doc("Sheet Size", doc.sheet_size) if doc.sheet_size else None
	settings = frappe.get_cached_doc("Print Suite Settings")
	cartons = compute_cartons(
		sheets_required=int(doc.sheets_required or 0),
		a4_equivalent_count=int(sheet.a4_equivalent_count or 0) if sheet else 0,
		gsm=float(doc.gsm or 0),
		sheets_per_carton=int(settings.sheets_per_carton or 0),
	)

	job_values = dict(
		sheets_required=int(doc.sheets_required or 0),
		quantity=int(doc.quantity or 0),
		area_cm2=float(doc.die_area_cm2 or 0),
		colours=int(doc.colours_front or 0) + int(doc.colours_back or 0),
		sides=int(doc.glue_sides or 0),
		hours=0,
		cartons=cartons,
	)

	total = 0.0
	for row in doc.applied_cost_drivers:
		if not row.enabled:
			row.computed_cost = 0
			row.source = "Calculated"
			continue

		driver = frappe.get_cached_doc("Cost Driver", row.cost_driver)
		is_die_like = any(k in driver.name.lower() for k in _DIE_LIKE_KEYWORDS)
		is_cutting_like = any(k in driver.name.lower() for k in _CUTTING_LIKE_KEYWORDS)
		is_printing_like = any(k in driver.name.lower() for k in _PRINTING_LIKE_KEYWORDS)

		# Die-reuse rule, confirmed directly by Golden Arrow's estimator:
		# repeat customers don't pay for the die again on a reorder.
		if doc.reusing_existing_die and is_die_like:
			row.computed_cost = 0
			row.source = "Calculated"
			continue

		# Manual override, confirmed real need (Talha: Artwork and
		# Packing sometimes need a one-off different number - built
		# generally for any row, not just those two, since any Cost Item
		# could plausibly need the same - e.g. Packing when box capacity
		# depends on paper weight AND which of several real box sizes is
		# used, not something one formula should guess at). Gated on
		# cost_override_enabled, NOT a truthy check on cost_override
		# itself - Currency fields default to 0.0, not None, so a bare
		# `if row.cost_override:` would silently ignore a deliberate
		# override of exactly 0 (same bug class already caught and fixed
		# on waste_pct_override - fixed here too, 2026-08-19).
		if row.cost_override_enabled:
			row.computed_cost = round(float(row.cost_override or 0), 2)
			row.source = "Manual Override"
			total += row.computed_cost
			continue

		row_job_values = dict(job_values)
		if is_die_like:
			# Confirmed real by Mofeed, 2026-08-19, but flagged as NOT
			# universal: normally a die/frame is cut against the FULL
			# press sheet, not just the footprint of the pieces
			# actually extracted - whatever's left over after pulling
			# the ups is wasted, so the whole sheet's area gets
			# charged regardless of how many ups fit on it. But this
			# doesn't hold for every job (e.g. leftover sheet area
			# that genuinely gets reused elsewhere), so it's gated on
			# doc.die_uses_full_sheet_area (defaults True) rather than
			# applied unconditionally. When off, or when no Sheet Size
			# is set yet, falls back to the older per-piece x ups
			# model. Verified: a 48x33cm piece at 4-up on a 70x100
			# sheet - full-sheet mode gives 7,000 cm² (matching
			# Mofeed's real 1,050.00 SAR); per-piece x ups mode gives
			# 6,336 cm² (950.40 SAR), undercounting whenever the ups
			# don't perfectly tile the sheet.
			use_full_sheet = doc.get("die_uses_full_sheet_area", 1)
			if use_full_sheet and sheet:
				row_job_values["area_cm2"] = (sheet.width_cm or 0) * (sheet.height_cm or 0)
			else:
				row_job_values["area_cm2"] = row_job_values["area_cm2"] * (doc.ups or 1)
		if is_printing_like and doc.get("double_sided"):
			# Confirmed real gap (Talha, 2026-08-19): a sheet printed on
			# both sides needs two passes through the press, doubling
			# the effective sheet-equivalent volume BEFORE the tier
			# lookup - not just doubling the final cost - since it's a
			# declining-rate table, doubled volume can land in a
			# cheaper tier bracket entirely. Independent of Colours
			# Back (a job can reuse one plate set on both sides via
			# Work and Turn and still need double the press time).
			row_job_values["sheets_required"] = row_job_values["sheets_required"] * 2

		tiers = [(t.qty_from, t.qty_to, t.rate) for t in driver.tiers] if driver.is_tiered else None
		cost = compute_cost_driver(
			measurement_basis=driver.measurement_basis,
			fixed_setup_cost=driver.fixed_setup_cost or 0,
			is_tiered=bool(driver.is_tiered),
			rate=driver.rate or 0,
			tiers=tiers,
			decline_start_qty=driver.decline_start_qty or 0,
			decline_start_rate=driver.decline_start_rate or 0,
			decline_floor_qty=driver.decline_floor_qty or 0,
			decline_floor_rate=driver.decline_floor_rate or 0,
			**row_job_values,
		)
		if is_cutting_like:
			cost = cost / (doc.ups or 1)
		row.computed_cost = round(cost, 2)
		row.source = "Calculated"
		total += cost

	doc.driver_costs_total = round(total, 2)


def enforce_template_requirements(doc):
	"""Confirmed real need (Talha, 2026-08-19): make sure a required
	cost can't be silently switched off, and a cost the formula can't
	be trusted for (Packing on Flyer - Mofeed picks the box by eye, no
	fixed rule) can't be saved without a human actually reviewing and
	entering the real number. Called from validate(), so this genuinely
	blocks the save - not just a warning someone can dismiss and
	forget. Reads the template's per-line flags fresh each time rather
	than trusting anything cached on the row, since the template is the
	one source of truth for what THIS product type actually needs."""
	if not doc.product_template:
		return
	template_lines = {
		line.cost_driver: line
		for line in frappe.get_all("Template Cost Driver Line",
			filters={"parent": doc.product_template},
			fields=["cost_driver", "required", "needs_manual_confirmation"])
	}
	for row in doc.applied_cost_drivers:
		line = template_lines.get(row.cost_driver)
		if not line:
			continue
		if line.required and not row.enabled:
			frappe.throw(
				f"{row.cost_driver} is required for {doc.product_template} jobs and can't be "
				f"turned off for this estimate."
			)
		if line.needs_manual_confirmation and row.enabled and not row.cost_override_enabled:
			frappe.throw(
				f"{row.cost_driver} needs a manually confirmed number for {doc.product_template} "
				f"jobs - the formula alone isn't reliable enough here. Tick 'Override This Cost' "
				f"on the {row.cost_driver} row and enter the real figure before saving."
			)


def _tier_rate_used(tiers, qty):
	for qty_from, qty_to, rate in tiers:
		if qty_from <= qty <= qty_to:
			return rate
	return tiers[-1][2] if tiers else 0


def _rate_description(driver, doc, row):
	"""Human-readable 'what rate did we actually use' string, for the
	reconciliation table - the whole point is Mofeed can read this and
	say yes/no to each number without opening a single Cost Driver
	record himself."""
	if row.cost_override_enabled:
		return "Manual override"

	basis = driver.measurement_basis
	fixed = driver.fixed_setup_cost or 0

	if driver.is_tiered:
		basis_qty = doc.sheets_required if basis == "Per 1000 Sheets" else doc.quantity
		basis_qty = basis_qty or 0
		is_printing_like = any(k in driver.name.lower() for k in _PRINTING_LIKE_KEYWORDS)
		if is_printing_like and basis == "Per 1000 Sheets" and doc.get("double_sided"):
			basis_qty = basis_qty * 2
		tiers = [(t.qty_from, t.qty_to, t.rate) for t in driver.tiers]
		rate = _tier_rate_used(tiers, basis_qty)
		fixed_part = f"{fixed:g} fixed + " if fixed else ""
		return f"{fixed_part}{rate:g} SAR/1000 (tier)"

	if basis == "Per Sheet (Declining Rate)":
		from bot_print_suite.estimation.cost_driver_engine import _linear_decline_rate
		rate = _linear_decline_rate(doc.sheets_required or 0, driver.decline_start_qty or 0,
			driver.decline_start_rate or 0, driver.decline_floor_qty or 0, driver.decline_floor_rate or 0)
		return f"{rate:.4g} SAR/sheet (sliding {driver.decline_start_rate:g}\u2192{driver.decline_floor_rate:g})"

	rate = driver.rate or 0
	unit_word = {
		"Per cm2": "cm\u00b2", "Per Colour": "colour", "Per Side": "side",
		"Per Sheet": "sheet", "Per Hour": "hour", "Per Carton": "carton",
	}.get(basis)
	if unit_word:
		return f"{rate:g} SAR/{unit_word}"
	if basis == "Flat Fee":
		return f"{rate:g} SAR flat"
	return f"{rate:g}"


def _quantity_description(driver, doc):
	"""The multiplier actually used for this job - the other half of
	'can Mofeed verify this number himself'."""
	basis = driver.measurement_basis
	if basis == "Per cm2":
		is_die_like = any(k in driver.name.lower() for k in _DIE_LIKE_KEYWORDS)
		if is_die_like:
			sheet = frappe.get_cached_doc("Sheet Size", doc.sheet_size) if doc.sheet_size else None
			use_full_sheet = doc.get("die_uses_full_sheet_area", 1)
			if use_full_sheet and sheet:
				sheet_area = (sheet.width_cm or 0) * (sheet.height_cm or 0)
				return f"{sheet.width_cm:g}\u00d7{sheet.height_cm:g}cm sheet = {sheet_area:g} cm\u00b2"
			total_area = (doc.die_area_cm2 or 0) * (doc.ups or 1)
			return f"{doc.die_area_cm2:g} cm\u00b2 \u00d7 {doc.ups or 1} ups = {total_area:g} cm\u00b2"
		return f"{doc.die_area_cm2:g} cm\u00b2"
	if basis == "Per Colour":
		return f"{(doc.colours_front or 0) + (doc.colours_back or 0):g} colours"
	if basis == "Per Side":
		return f"{doc.glue_sides or 0:g} sides"
	if basis in ("Per 1000 Sheets", "Per Sheet", "Per Sheet (Declining Rate)"):
		is_printing_like = any(k in driver.name.lower() for k in _PRINTING_LIKE_KEYWORDS)
		if is_printing_like and doc.get("double_sided"):
			doubled = (doc.sheets_required or 0) * 2
			return f"{doc.sheets_required or 0:,} sheets \u00d7 2 (double-sided) = {doubled:,} sheet-sides"
		return f"{doc.sheets_required or 0:,} sheets"
	if basis == "Per Carton":
		from bot_print_suite.estimation.cost_driver_engine import compute_cartons
		sheet = frappe.get_cached_doc("Sheet Size", doc.sheet_size) if doc.sheet_size else None
		settings = frappe.get_cached_doc("Print Suite Settings")
		cartons = compute_cartons(
			sheets_required=doc.sheets_required or 0,
			a4_equivalent_count=(sheet.a4_equivalent_count or 0) if sheet else 0,
			gsm=doc.gsm or 0,
			sheets_per_carton=settings.sheets_per_carton or 0,
		)
		return f"{cartons:,.1f} cartons"
	if basis == "Per 1000 Pieces":
		is_cutting_like = any(k in driver.name.lower() for k in _CUTTING_LIKE_KEYWORDS)
		if is_cutting_like:
			return f"{doc.quantity or 0:,} pieces \u00f7 {doc.ups or 1} ups"
		return f"{doc.quantity or 0:,} pieces"
	return "-"


def _formula_description(driver, doc, row, computed_cost):
	"""The literal worked formula, numbers plugged in - this is the
	answer to 'I need the exact way the number was created,' not just
	the rate and quantity separately (which still makes someone do the
	multiplication themselves)."""
	if row.cost_override_enabled:
		return f"Manually entered: {float(row.cost_override or 0):,.2f} (replaces the normal calculation entirely)"

	basis = driver.measurement_basis
	fixed = driver.fixed_setup_cost or 0

	if basis == "Flat Fee":
		return f"{driver.rate or 0:,.2f} SAR flat \u2014 no calculation, always this amount"

	if basis == "Per cm2":
		is_die_like = any(k in driver.name.lower() for k in _DIE_LIKE_KEYWORDS)
		if is_die_like:
			sheet = frappe.get_cached_doc("Sheet Size", doc.sheet_size) if doc.sheet_size else None
			use_full_sheet = doc.get("die_uses_full_sheet_area", 1)
			if use_full_sheet and sheet:
				area = (sheet.width_cm or 0) * (sheet.height_cm or 0)
				note = f" (full {sheet.width_cm:g}\u00d7{sheet.height_cm:g}cm sheet, not just the {doc.ups or 1} ups extracted from it)"
			else:
				area = (doc.die_area_cm2 or 0) * (doc.ups or 1)
				note = f" ({doc.die_area_cm2:g} cm\u00b2 \u00d7 {doc.ups or 1} ups)"
			return f"{driver.rate:g} SAR/cm\u00b2 \u00d7 {area:,.0f} cm\u00b2{note} = {computed_cost:,.2f} SAR"
		area = doc.die_area_cm2 or 0
		return f"{driver.rate:g} SAR/cm\u00b2 \u00d7 {area:,.0f} cm\u00b2 = {computed_cost:,.2f} SAR"

	if basis == "Per Colour":
		n = (doc.colours_front or 0) + (doc.colours_back or 0)
		return f"{driver.rate:g} SAR/colour \u00d7 {n} colours = {computed_cost:,.2f} SAR"

	if basis == "Per Side":
		return f"{driver.rate:g} SAR/side \u00d7 {doc.glue_sides or 0} sides = {computed_cost:,.2f} SAR"

	if basis == "Per Hour":
		return f"{driver.rate:g} SAR/hour \u00d7 hours = {computed_cost:,.2f} SAR"

	if basis == "Per Sheet (Declining Rate)":
		from bot_print_suite.estimation.cost_driver_engine import _linear_decline_rate
		qty = doc.sheets_required or 0
		rate = _linear_decline_rate(qty, driver.decline_start_qty or 0, driver.decline_start_rate or 0,
			driver.decline_floor_qty or 0, driver.decline_floor_rate or 0)
		return (f"{qty:,} sheets \u00d7 {rate:.4g} SAR/sheet (sliding {driver.decline_start_rate:g} at "
			f"{driver.decline_start_qty:,} \u2192 {driver.decline_floor_rate:g} at {driver.decline_floor_qty:,}) "
			f"= {computed_cost:,.2f} SAR")

	if basis == "Per Carton":
		from bot_print_suite.estimation.cost_driver_engine import compute_cartons
		sheet = frappe.get_cached_doc("Sheet Size", doc.sheet_size) if doc.sheet_size else None
		settings = frappe.get_cached_doc("Print Suite Settings")
		cartons = compute_cartons(
			sheets_required=doc.sheets_required or 0,
			a4_equivalent_count=(sheet.a4_equivalent_count or 0) if sheet else 0,
			gsm=doc.gsm or 0,
			sheets_per_carton=settings.sheets_per_carton or 0,
		)
		a4c = (sheet.a4_equivalent_count or 0) if sheet else 0
		return (f"({doc.sheets_required or 0:,} sheets \u00d7 {a4c} A4-equiv \u00d7 {doc.gsm or 0:g}gsm \u00f7 100) "
			f"\u00f7 {settings.sheets_per_carton or 0:,} sheets/carton = {cartons:,.1f} cartons \u00d7 "
			f"{driver.rate:g} SAR/carton = {computed_cost:,.2f} SAR")

	if basis in ("Per 1000 Sheets", "Per 1000 Pieces", "Per Sheet"):
		qty = doc.sheets_required if basis in ("Per 1000 Sheets", "Per Sheet") else doc.quantity
		qty = qty or 0
		if basis == "Per Sheet":
			return f"{driver.rate:g} SAR/sheet \u00d7 {qty:,} sheets = {computed_cost:,.2f} SAR"
		is_cutting_like = any(k in driver.name.lower() for k in _CUTTING_LIKE_KEYWORDS)
		is_printing_like = any(k in driver.name.lower() for k in _PRINTING_LIKE_KEYWORDS)
		double_sided_note = ""
		if is_printing_like and basis == "Per 1000 Sheets" and doc.get("double_sided"):
			double_sided_note = f" ({doc.sheets_required or 0:,} sheets \u00d7 2, double-sided)"
			qty = qty * 2
		ups = doc.ups or 1
		if driver.is_tiered:
			tiers = [(t.qty_from, t.qty_to, t.rate) for t in driver.tiers]
			rate = _tier_rate_used(tiers, qty)
			unit = "sheets" if basis == "Per 1000 Sheets" else "pieces"
			variable_part = (qty / 1000) * rate
			raw = fixed + variable_part
			if is_cutting_like:
				fixed_part = f"{fixed:g} fixed + " if fixed else ""
				return (f"({fixed_part}{qty:,} {unit} \u00f7 1000 \u00d7 {rate:g}) \u00f7 {ups} ups "
					f"= {raw:,.2f} \u00f7 {ups} = {computed_cost:,.2f} SAR")
			if fixed:
				return (f"{fixed:g} fixed + ({qty:,} {unit}{double_sided_note} \u00f7 1000 \u00d7 {rate:g}) "
					f"= {fixed:g} + {variable_part:,.2f} = {computed_cost:,.2f} SAR")
			return f"{qty:,} {unit}{double_sided_note} \u00f7 1000 \u00d7 {rate:g} = {computed_cost:,.2f} SAR"
		unit = "sheets" if basis == "Per 1000 Sheets" else "pieces"
		rate = driver.rate or 0
		variable_part = (qty / 1000) * rate
		raw = fixed + variable_part
		if is_cutting_like:
			fixed_part = f"{fixed:g} fixed + " if fixed else ""
			return (f"({fixed_part}{qty:,} {unit} \u00f7 1000 \u00d7 {rate:g}) \u00f7 {ups} ups "
				f"= {raw:,.2f} \u00f7 {ups} = {computed_cost:,.2f} SAR")
		if fixed:
			return (f"{fixed:g} fixed + ({qty:,} {unit} \u00f7 1000 \u00d7 {rate:g}) "
				f"= {computed_cost:,.2f} SAR")
		return f"{qty:,} {unit} \u00f7 1000 \u00d7 {rate:g} = {computed_cost:,.2f} SAR"

	return f"= {computed_cost:,.2f} SAR"


def build_reconciliation_table(doc):
	"""Builds the full, printable cost reconciliation table - EVERY
	component (Paper included, which isn't a Cost Driver at all) with
	its rate, quantity and total, ending in Subtotal. Meant to be looked
	at directly by the customer's own estimator to confirm or dispute
	each line - the whole point is nothing here should require opening
	another record to understand."""
	rows = []

	paper_type_name = doc.paper_type or "-"
	cost_per_sheet = round((doc.paper_cost or 0) / doc.sheets_required, 4) if doc.sheets_required else 0
	paper_formula = f"{cost_per_sheet:g} SAR/sheet \u00d7 {doc.sheets_required or 0:,} sheets = {doc.paper_cost or 0:,.2f} SAR"
	rows.append(("Paper (\u0648\u0631\u0642)", paper_type_name, f"{cost_per_sheet:g} SAR/sheet",
		f"{doc.sheets_required or 0:,} sheets", doc.paper_cost or 0, paper_formula))

	for row in (doc.applied_cost_drivers or []):
		if not row.enabled:
			continue
		driver = frappe.get_cached_doc("Cost Driver", row.cost_driver)
		if doc.reusing_existing_die and any(k in driver.name.lower() for k in _DIE_LIKE_KEYWORDS):
			continue
		rows.append((driver.name, driver.measurement_basis,
			_rate_description(driver, doc, row), _quantity_description(driver, doc), row.computed_cost or 0,
			_formula_description(driver, doc, row, row.computed_cost or 0)))

	if doc.freight_cost:
		rows.append(("Freight (\u0627\u0644\u0634\u062d\u0646)", "-", "-", "-", doc.freight_cost,
			f"Entered directly: {doc.freight_cost:,.2f} SAR"))

	html = ["<div style='font-size:12px;'>",
		"<table class='table table-bordered' style='margin-bottom:8px;'>",
		"<thead><tr style='background:#F2F4F8;'>",
		"<th>Item</th><th>Basis</th><th>Rate Used</th><th>Quantity</th><th style='text-align:right;'>Total (SAR)</th>",
		"</tr></thead><tbody>"]
	for name, basis, rate_desc, qty_desc, total, formula in rows:
		safe_formula = formula.replace('"', "&quot;")
		icon = (f"<span class='formula-icon' data-formula=\"{safe_formula}\" data-item=\"{name}\" "
			f"style='cursor:pointer;color:#8d99a6;font-size:12px;"
			f"margin-right:4px;text-decoration:underline;text-decoration-style:dotted;'>\u24d8</span>")
		html.append(f"<tr><td>{name}</td><td>{basis}</td><td>{rate_desc}</td>"
			f"<td>{qty_desc}</td><td style='text-align:right;'>{icon}{total:,.2f}</td></tr>")
	html.append(f"<tr style='font-weight:bold;background:#F7F8FA;'>"
		f"<td colspan='4'>Subtotal (\u0627\u0644\u0645\u062c\u0645\u0648\u0639)</td>"
		f"<td style='text-align:right;'>{doc.subtotal or 0:,.2f}</td></tr>")
	html.append("</tbody></table></div>")
	return "".join(html)
