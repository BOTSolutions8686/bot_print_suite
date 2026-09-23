"""
BOT Print Suite - Print Estimation Engine

All money/geometry math for print job costing lives here, per PLAN.md's
"Money logic - non-negotiable" rule: one module, server-side, no
duplicated formulas in client scripts.

Pure functions (ups_per_sheet, calc_estimate) take plain values and return
plain values/dicts - no frappe.* calls - so they can be unit tested with
hand-derived expected values (see tests/test_engine.py). compute_estimate()
is the only function that touches a Frappe document/DB.
"""

import math


def lookup_confirmed_ups(sheet_w_mm, sheet_h_mm, item_w_mm, item_h_mm, references):
	"""Checks a list of REAL, CONFIRMED (sheet, finished-item) -> ups
	results before falling back to pure geometry. This exists because
	geometry alone doesn't always match real practice - confirmed real
	example (Talha/Mofeed, 2026-08-19): a 21x29.7cm A4 flyer on a
	70x100cm sheet computes 9-up by pure tiling, but Mofeed's real
	number is 8-up, matching the well-known published "8-up A4"
	imposition convention (e.g. SRA1 640x900mm -> 8-up A4, a named
	industry-standard scheme, not a one-off preference) - tried every
	realistic gripper/colour-bar/trim/gutter combination and NONE
	naturally reject the tighter 9-up fit without inventing implausible
	margin constants, so this genuinely isn't a geometry-modeling gap.

	This is an EXACT match on real confirmed combinations, not a fuzzy
	"sheet size class" heuristic - deliberately narrow, so an unmatched
	combination correctly falls through to the geometric calculation
	rather than guessing whether some other size counts as "close
	enough" to a confirmed one. `references` is a list of
	(sheet_w_mm, sheet_h_mm, item_w_mm, item_h_mm, ups, source) tuples;
	item dimensions match in either orientation, since a piece given as
	210x297 is the same physical size as one given as 297x210. Returns
	(ups, source) on a match, else None.
	"""
	def _close(a, b, tol_mm=0.5):
		return abs(a - b) <= tol_mm

	for ref_sw, ref_sh, ref_iw, ref_ih, ups, source in references:
		if not (_close(sheet_w_mm, ref_sw) and _close(sheet_h_mm, ref_sh)):
			continue
		same_orientation = _close(item_w_mm, ref_iw) and _close(item_h_mm, ref_ih)
		rotated = _close(item_w_mm, ref_ih) and _close(item_h_mm, ref_iw)
		if same_orientation or rotated:
			return ups, source
	return None


def ups_per_sheet(sheet_w_mm, sheet_h_mm, item_w_mm, item_h_mm, gripper_margin_mm):
	"""Ups-per-sheet via simple imposition: divide the gripper-reduced sheet
	by the (trim + bleed*2 + gutter) item size, floor to whole units, and
	take the better of the two orientations. Not a nesting optimizer -
	that's Phase 2 (PLAN.md).
	"""
	usable_w = sheet_w_mm - (2 * gripper_margin_mm)
	usable_h = sheet_h_mm - (2 * gripper_margin_mm)

	def _ups(iw, ih):
		if iw <= 0 or ih <= 0:
			return 0
		cols = math.floor(usable_w / iw)
		rows = math.floor(usable_h / ih)
		return max(cols, 0) * max(rows, 0)

	upright = _ups(item_w_mm, item_h_mm)
	rotated = _ups(item_h_mm, item_w_mm)
	return max(upright, rotated)


def sheet_weight_kg(sheet_w_mm, sheet_h_mm, gsm):
	"""KSA mills quote paper per tonne. weight(kg) = area(m2) * gsm / 1000."""
	area_m2 = (sheet_w_mm / 1000) * (sheet_h_mm / 1000)
	return area_m2 * gsm / 1000


def paper_cost_per_sheet(sheet_w_mm, sheet_h_mm, gsm, rate_per_tonne):
	weight_kg = sheet_weight_kg(sheet_w_mm, sheet_h_mm, gsm)
	rate_per_kg = rate_per_tonne / 1000
	return weight_kg * rate_per_kg


def compute_sheets_and_paper(qty, ups, makeready_sheets, run_waste_pct,
		sheet_w_mm, sheet_h_mm, gsm, paper_rate_per_tonne, direct_cost_per_sheet=None):
	"""direct_cost_per_sheet: when a real Paper Type record exists
	(rate confirmed directly from the estimator, using their own real
	reems/sheets-per-reem trade convention), use that EXACT per-sheet
	cost instead of re-deriving one from raw area x gsm physics - the
	two can differ slightly (confirmed: ~0.2% on a real reconciliation),
	and matching the estimator's own real number takes priority over a
	theoretically-derived one. Falls back to the area-based formula
	(unchanged, still covered by the original golden tests) when no
	matching Paper Type exists yet - existing estimates are unaffected.
	"""
	if ups <= 0:
		return 0, 0.0
	base_sheets = math.ceil(qty / ups)
	waste_sheets = round(base_sheets * (run_waste_pct / 100))
	sheets_required = base_sheets + makeready_sheets + waste_sheets
	if direct_cost_per_sheet is not None:
		cost_per_sheet = direct_cost_per_sheet
	else:
		cost_per_sheet = paper_cost_per_sheet(sheet_w_mm, sheet_h_mm, gsm, paper_rate_per_tonne)
	return sheets_required, sheets_required * cost_per_sheet


def compute_impressions(sheets_required, colours_front, colours_back, printing_method):
	"""Sheetwise: sheet printed once per side -> impressions = sheets * sides.
	Work and Turn: sheet passes through the press twice (front then flip
	for back) using ONE plate set - impressions = sheets * 2, but plates
	(see compute_plates) are halved, not impressions."""
	sides = 2 if colours_back > 0 else 1
	return sheets_required * sides


def compute_plates(colours_front, colours_back, printing_method):
	total_colours = colours_front + colours_back
	if printing_method == "Work and Turn" and colours_back > 0:
		# one shared plate set prints both sides via work-and-turn
		return colours_front
	return total_colours


def compute_ink_cost(sheets_required, sheet_w_mm, sheet_h_mm, colours_front,
		colours_back, coverage_factor, ink_rate_per_sqm):
	sheet_area_m2 = (sheet_w_mm / 1000) * (sheet_h_mm / 1000)
	total_colours = colours_front + colours_back
	return sheets_required * sheet_area_m2 * coverage_factor * total_colours * ink_rate_per_sqm


def compute_press_run_cost(impressions, makeready_cost, running_rate_per_1000):
	return makeready_cost + (impressions / 1000) * running_rate_per_1000


def compute_finishing_cost(finishing_lines, sheets_required, sheet_w_mm, sheet_h_mm):
	"""finishing_lines: list of (unit_basis, rate). Returns (total, per_line)."""
	sheet_area_m2 = (sheet_w_mm / 1000) * (sheet_h_mm / 1000)
	per_line = []
	total = 0.0
	for unit_basis, rate in finishing_lines:
		if unit_basis == "Per 1000 Sheets":
			cost = (sheets_required / 1000) * rate
		else:  # Per Sqm
			cost = sheets_required * sheet_area_m2 * rate
		per_line.append(cost)
		total += cost
	return total, per_line


def calc_estimate(*, finished_w_mm, finished_h_mm, qty, colours_front, colours_back,
		printing_method, sheet_w_mm, sheet_h_mm, gripper_margin_mm, bleed_mm, gutter_mm,
		makeready_sheets, run_waste_pct, makeready_cost, running_rate_per_1000,
		paper_rate_per_tonne, gsm, plate_rate, coverage_factor, ink_rate_per_sqm,
		finishing_lines, die_cost, freight_cost, margin_pct, direct_cost_per_sheet=None,
		ups_override=None, confirmed_ups_references=None):
	"""Pure orchestrator: plain values in, plain dict out. This is what the
	golden tests call directly - no frappe.* dependency."""
	item_w = finished_w_mm + (2 * bleed_mm) + gutter_mm
	item_h = finished_h_mm + (2 * bleed_mm) + gutter_mm

	# Priority: an explicit per-job ups_override (a specific, documented
	# reason for THIS job) beats a confirmed reference (a general, reusable
	# real result), which beats raw geometry (the fallback for combinations
	# nobody's confirmed yet). ups_override, confirmed real need (Talha,
	# 2026-08-19): pure geometry - even corrected for a real gripper margin
	# - doesn't always match a real printer's practical number (control-
	# strip reservation, press quirks, operator judgement not captured by
	# clean tiling math). None means "no override" - 0 ups makes no
	# physical sense, so there's no ambiguous-zero problem here the way
	# Currency fields had.
	confirmed = lookup_confirmed_ups(sheet_w_mm, sheet_h_mm, item_w, item_h,
		confirmed_ups_references or [])
	ups_source = "geometry"
	if ups_override is not None:
		ups = ups_override
		ups_source = "override"
	elif confirmed is not None:
		ups, _confirmed_source = confirmed
		ups_source = "confirmed"
	else:
		ups = ups_per_sheet(sheet_w_mm, sheet_h_mm, item_w, item_h, gripper_margin_mm)

	sheets_required, paper_cost = compute_sheets_and_paper(
		qty, ups, makeready_sheets, run_waste_pct, sheet_w_mm, sheet_h_mm, gsm, paper_rate_per_tonne,
		direct_cost_per_sheet=direct_cost_per_sheet)

	impressions = compute_impressions(sheets_required, colours_front, colours_back, printing_method)
	plates = compute_plates(colours_front, colours_back, printing_method)
	plate_cost = plates * plate_rate

	ink_cost = compute_ink_cost(sheets_required, sheet_w_mm, sheet_h_mm,
		colours_front, colours_back, coverage_factor, ink_rate_per_sqm)

	press_run_cost = compute_press_run_cost(impressions, makeready_cost, running_rate_per_1000)

	finishing_cost_total, finishing_per_line = compute_finishing_cost(
		finishing_lines, sheets_required, sheet_w_mm, sheet_h_mm)

	subtotal = (paper_cost + ink_cost + plate_cost + press_run_cost
		+ finishing_cost_total + die_cost + freight_cost)
	sell_price = subtotal * (1 + margin_pct / 100)

	return {
		"ups": ups,
		"ups_source": ups_source,
		"sheets_required": sheets_required,
		"plates_count": plates,
		"paper_cost": round(paper_cost, 2),
		"ink_cost": round(ink_cost, 2),
		"plate_cost": round(plate_cost, 2),
		"press_run_cost": round(press_run_cost, 2),
		"finishing_cost_total": round(finishing_cost_total, 2),
		"finishing_per_line": [round(c, 2) for c in finishing_per_line],
		"subtotal": round(subtotal, 2),
		"sell_price": round(sell_price, 2),
	}


# TODO(Phase 1, step 4d): once auto-created paper Items exist, source this
# from Item Price instead of this placeholder constant. Tracked in PLAN.md
# section 4d (auto-create missing paper Items).
_DEFAULT_PAPER_RATE_PER_TONNE = 3000

_COVERAGE_SETTINGS_FIELD = {
	"Light": "ink_coverage_light",
	"Medium": "ink_coverage_medium",
	"Heavy": "ink_coverage_heavy",
}


def compute_estimate(doc):
	"""Frappe-facing wrapper: reads the Print Estimate doc + its linked
	masters (Press Profile, Print Suite Settings, Finishing Rate Card),
	calls the pure calc_estimate(), and writes results back onto doc.
	Only function in this module allowed to touch frappe.* / the DB.
	"""
	import frappe

	press = frappe.get_cached_doc("Press Profile", doc.press)
	settings = frappe.get_cached_doc("Print Suite Settings")
	sheet = frappe.get_cached_doc("Sheet Size", doc.sheet_size)

	# Confirmed imposition results, real (sheet, finished-size) -> ups
	# combinations someone has actually verified, checked before falling
	# back to raw geometry (see lookup_confirmed_ups). Only entries for
	# THIS job's sheet are fetched - a small, cheap query, and it means a
	# new Imposition Reference record takes effect on every future
	# estimate using that sheet without any code change.
	confirmed_ups_references = [
		(sheet.width_mm, sheet.height_mm, r.finished_width_cm * 10, r.finished_height_cm * 10,
			r.confirmed_ups, r.source)
		for r in frappe.get_all("Imposition Reference",
			filters={"sheet_size": doc.sheet_size},
			fields=["finished_width_cm", "finished_height_cm", "confirmed_ups", "source"])
	] if doc.sheet_size else []

	coverage_factor = getattr(settings, _COVERAGE_SETTINGS_FIELD["Medium"])  # ink_coverage removed from the templated-only form - Ink Cost is unused/hidden for templated estimates anyway, this value never surfaces

	paper_rate_per_tonne = _DEFAULT_PAPER_RATE_PER_TONNE
	if doc.paper_type:
		# Direct link - the real, current way. No typo risk between
		# Substrate/GSM text and a Paper Type record name.
		direct_cost_per_sheet = frappe.db.get_value("Paper Type", doc.paper_type, "cost_per_sheet")
	else:
		# Backward compatibility only - estimates created before the
		# Paper Type link existed, still keyed by free-text Substrate/GSM.
		direct_cost_per_sheet = frappe.db.get_value(
			"Paper Type", {"paper_name": doc.substrate, "gsm": doc.gsm}, "cost_per_sheet")
	# direct_cost_per_sheet is None if no matching Paper Type exists yet -
	# calc_estimate() falls back to the old area x gsm formula in that
	# case, so estimates for substrates we haven't calibrated yet still
	# work exactly as before, just less precisely.

	# finishing_operations removed from the templated-only form -
	# Lamination/Foiling/UV/Die-cut/Gluing are now priced as Cost Items
	# via Cost Driver records instead. calc_estimate() still accepts
	# finishing_lines as a parameter (unchanged, still covered by its
	# own golden tests) - it's just always empty from the doc side now.
	finishing_lines = []

	def _run(qty):
		# Explicit float()/int() casts on every doc-sourced number below -
		# NOT redundant. Frappe's client-side JS does not always send a
		# field's DEFAULT value (as opposed to a value the user actually
		# typed) as the right Python type - margin_pct's default of "20"
		# arrived here as the literal string "20" on a fresh, never-before-
		# saved estimate, and margin_pct / 100 crashed with exactly this
		# TypeError. Every one of THIS module's own tests set these values
		# explicitly in Python (always real numbers), so this never got
		# exercised until a real save-from-the-actual-form did. Casting
		# defensively here, at the one place all these values funnel
		# through, rather than trusting the caller's types.
		return calc_estimate(
			finished_w_mm=float(doc.finished_size_w), finished_h_mm=float(doc.finished_size_h),
			qty=int(qty), colours_front=int(doc.colours_front), colours_back=int(doc.colours_back or 0),
			printing_method="Sheetwise",  # printing_method removed from the templated-only form - Plate Cost Item prices plates directly, this value never surfaces
			sheet_w_mm=float(sheet.width_mm), sheet_h_mm=float(sheet.height_mm),
			gripper_margin_mm=float(press.gripper_margin_mm),
			bleed_mm=0.0, gutter_mm=0.0,  # removed from the form - Golden Arrow's real blank sizes already include whatever margin they need
			makeready_sheets=int(press.makeready_sheets or 0), run_waste_pct=float(doc.waste_pct_override or 0) if doc.get("waste_pct_override_enabled") else float(press.run_waste_pct or 0),
			makeready_cost=float(press.makeready_cost or 0), running_rate_per_1000=float(press.running_rate_per_1000 or 0),
			paper_rate_per_tonne=float(paper_rate_per_tonne), gsm=float(doc.gsm),
			plate_rate=float(settings.default_plate_rate or 0),
			coverage_factor=float(coverage_factor), ink_rate_per_sqm=float(settings.ink_rate_per_sqm or 0),
			finishing_lines=finishing_lines,
			die_cost=0.0, freight_cost=float(doc.freight_cost or 0),  # old die_cost field removed - Die/Frame Cost Item covers this now
			margin_pct=float(doc.margin_pct or 0),
			direct_cost_per_sheet=float(direct_cost_per_sheet) if direct_cost_per_sheet is not None else None,
			ups_override=int(doc.ups_override) if doc.get("ups_override_enabled") else None,
			confirmed_ups_references=confirmed_ups_references,
		)

	result = _run(doc.quantity)
	doc.ups = result["ups"]
	doc.sheets_required = result["sheets_required"]
	doc.paper_cost = result["paper_cost"]

	# Worked formulas for Ups per Sheet and Sheets Required - answers
	# "how was this number created" the same way the Cost Reconciliation
	# Table already does for the cost lines. Stored on the doc so the
	# client script can feed them into the same click-to-reveal icon
	# mechanism already built for field descriptions - real per-document
	# numbers, not the generic static text those fields had before.
	if doc.get("ups_override_enabled"):
		reason = doc.get("ups_override_reason") or "(no reason given)"
		doc.ups_formula = (
			f"Manually entered: {doc.ups} ups per sheet (replaces the geometric calculation "
			f"entirely).\nReason: {reason}"
		)
	elif result["ups_source"] == "confirmed":
		item_w = doc.finished_width_cm * 10
		item_h = doc.finished_height_cm * 10
		matched_source = next(
			(src for sw, sh, iw, ih, ups, src in confirmed_ups_references
				if abs(sw - sheet.width_mm) <= 0.5 and abs(sh - sheet.height_mm) <= 0.5
				and ((abs(iw - item_w) <= 0.5 and abs(ih - item_h) <= 0.5)
					or (abs(iw - item_h) <= 0.5 and abs(ih - item_w) <= 0.5))),
			"(source not found - check Imposition Reference records)")
		doc.ups_formula = (
			f"Matched a confirmed Imposition Reference: {doc.finished_width_cm:g}\u00d7"
			f"{doc.finished_height_cm:g}cm on a {sheet.width_cm:g}\u00d7{sheet.height_cm:g}cm sheet "
			f"= {doc.ups} ups per sheet, real and reusable (not derived from geometry for this job).\n\n"
			f"Source: {matched_source}"
		)
	else:
		gripper_cm = float(press.gripper_margin_mm or 0) / 10
		usable_w_cm = float(sheet.width_cm or 0) - 2 * gripper_cm
		usable_h_cm = float(sheet.height_cm or 0) - 2 * gripper_cm
		item_w_cm = doc.finished_width_cm or 0
		item_h_cm = doc.finished_height_cm or 0
		cols_a = int(usable_w_cm // item_w_cm) if item_w_cm else 0
		rows_a = int(usable_h_cm // item_h_cm) if item_h_cm else 0
		ups_a = cols_a * rows_a
		cols_b = int(usable_w_cm // item_h_cm) if item_h_cm else 0
		rows_b = int(usable_h_cm // item_w_cm) if item_w_cm else 0
		ups_b = cols_b * rows_b
		winner = "as-is" if ups_a >= ups_b else "rotated 90\u00b0"
		doc.ups_formula = (
			f"Sheet {sheet.width_cm:g}\u00d7{sheet.height_cm:g}cm, minus {gripper_cm:g}cm gripper margin on "
			f"each side of both dimensions = usable area {usable_w_cm:g}\u00d7{usable_h_cm:g}cm.\n\n"
			f"Tried as-is ({item_w_cm:g}\u00d7{item_h_cm:g}cm piece): "
			f"{cols_a} across \u00d7 {rows_a} down = {ups_a} ups.\n"
			f"Tried rotated ({item_h_cm:g}\u00d7{item_w_cm:g}cm piece): "
			f"{cols_b} across \u00d7 {rows_b} down = {ups_b} ups.\n\n"
			f"Better fit is {winner}: {doc.ups} ups per sheet.\n\n"
			f"No confirmed Imposition Reference exists for this exact sheet/size combination yet, "
			f"so this is raw geometry - it doesn't always match real practice (control-strip "
			f"reservation, press quirks). If Mofeed's real number differs, either use the Ups "
			f"Override below for just this job, or add an Imposition Reference record so every "
			f"future job with this exact sheet/size gets it automatically."
		)


	if doc.get("sheets_required_override"):
		doc.sheets_required_formula = (
			f"Entered directly: {int(doc.sheets_required_override):,} sheets "
			f"(skips the Ups/waste calculation below entirely)."
		)
	else:
		base_sheets = -(-int(doc.quantity or 0) // (doc.ups or 1)) if doc.ups else 0  # ceil division
		waste_pct = float(doc.waste_pct_override or 0) if doc.get("waste_pct_override_enabled") else float(press.run_waste_pct or 0)
		waste_sheets = round(base_sheets * (waste_pct / 100))
		makeready = int(press.makeready_sheets or 0)
		doc.sheets_required_formula = (
			f"Base sheets: {int(doc.quantity or 0):,} pieces \u00f7 {doc.ups} ups per sheet, "
			f"rounded up = {base_sheets:,} sheets.\n\n"
			f"+ {makeready} make-ready sheets ({press.press_name}'s fixed setup waste)\n"
			f"+ {waste_sheets:,} running waste ({waste_pct:g}% of {base_sheets:,} = {waste_sheets:,})\n\n"
			f"= {base_sheets:,} + {makeready} + {waste_sheets:,} = {doc.sheets_required:,} sheets."
		)

	# Sheets Required absolute override - confirmed real need (Talha:
	# sometimes Mofeed gives an exact sheet count directly, e.g. "3333
	# sheets", rather than a waste PERCENTAGE to calculate from). If set,
	# this REPLACES both Sheets Required and Paper Cost - recomputing
	# paper cost from the real per-sheet rate this job already used, so
	# the two numbers stay consistent with each other rather than one
	# being overridden and the other left stale.
	if doc.get("sheets_required_override"):
		cost_per_sheet = (doc.paper_cost / doc.sheets_required) if doc.sheets_required else 0
		doc.sheets_required = int(doc.sheets_required_override)
		doc.paper_cost = round(doc.sheets_required * cost_per_sheet, 2)
	# Note: Plates Count, Ink/Plate/Press Run/Finishing Cost, and per-line
	# finishing costs are still computed inside result (unchanged, still
	# covered by the original 11 golden tests that test calc_estimate()
	# directly) - they're just no longer written back onto the doc, since
	# those fields were removed from the templated-only form. Subtotal
	# and Sell Price below are overwritten again further down using the
	# Cost Items total instead - this assignment here is an intermediate
	# value, not the final one.
	doc.subtotal = result["subtotal"]
	doc.sell_price = result["sell_price"]

	doc.computed_breaks = []
	for brk in (doc.quantity_breaks or []):
		r = _run(brk.qty)
		doc.append("computed_breaks", {
			"qty": brk.qty,
			"sheets_required": r["sheets_required"],
			"subtotal": r["subtotal"],
			"sell_price": r["sell_price"],
		})
