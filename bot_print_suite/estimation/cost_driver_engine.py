"""
BOT Print Suite - Generic Cost Driver engine (PLAN.md Step 10).

Deliberately mirrors estimation/engine.py's own discipline: pure
functions here, no frappe.* calls, hand-derived golden tests against
Mofeed's real confirmed numbers (Golden Arrow's estimator) - not
invented numbers. compute_cost_driver_from_doc() at the bottom is the
only function meant to touch a Frappe document/DB.

Scope note, deliberate: Paper cost is NOT modelled as a Cost Driver
here. It stays in estimation/engine.py, because it genuinely depends on
real geometry (ups-per-sheet, waste-adjusted sheets required) that a
simple "rate x measurement" driver can't express, and that logic is
already built, tested, and correct. Cost Drivers exist for the OTHER
lines Mofeed's real data revealed: Plate, Printing, Die, Cutting, Glue,
Artwork, Packing - the lines that genuinely do vary in shape (some per
cm^2, some per 1000 sheets, some flat) and need to be reusable across
future product templates (cards, stickers), not hard-coded fields.
"""

import math


def _tier_rate(tiers, qty):
	"""tiers: list of (qty_from, qty_to, rate). Returns the rate for the
	tier that qty falls into. If qty falls in no tier, uses the last
	(highest) tier as a fallback rather than erroring - a job bigger than
	any tier we've been told about should still get *a* number, not a
	crash, though it's worth flagging for review in that case."""
	for qty_from, qty_to, rate in tiers:
		if qty_from <= qty <= qty_to:
			return rate
	return tiers[-1][2] if tiers else 0


def _linear_decline_rate(qty, start_qty, start_rate, floor_qty, floor_rate):
	"""Straight-line interpolation between two confirmed real points -
	e.g. Lamination: 0.80 SAR/sheet confirmed at 1,000 sheets, 0.55
	SAR/sheet confirmed as the floor at 150,000 sheets (Mofeed, real
	numbers). Below start_qty: start_rate exactly. At/above floor_qty:
	floor_rate exactly, never lower. Between the two: straight line -
	the model with the fewest invented assumptions given only 2 real
	data points (as opposed to guessing intermediate tier breakpoints
	the way Cutting/Printing's discrete tiers do, which needed 5 real
	points to justify)."""
	if floor_qty <= start_qty:
		return floor_rate
	if qty <= start_qty:
		return start_rate
	if qty >= floor_qty:
		return floor_rate
	frac = (qty - start_qty) / (floor_qty - start_qty)
	return start_rate + frac * (floor_rate - start_rate)


def compute_cartons(sheets_required, a4_equivalent_count, gsm, sheets_per_carton):
	"""Mofeed's real packing convention (Talha, 2026-08-19), step by
	step: press sheets -> A4-equivalent count (a per-sheet-size counting
	factor, not a strict geometric imposition) -> GSM-normalized by
	dividing by 100 (so heavier stock takes proportionally more cartons)
	-> divided by how many of those normalized units fit in one carton.
	Verified against his real worked example: 125,000 sheets, 8
	A4-equivalents/sheet, 300gsm, 3000/carton -> exactly 1,000 cartons."""
	if sheets_per_carton <= 0:
		return 0
	normalized_units = sheets_required * a4_equivalent_count * (gsm / 100)
	return normalized_units / sheets_per_carton


def compute_cost_driver(*, measurement_basis, fixed_setup_cost=0, is_tiered=False,
		rate=0, tiers=None, sheets_required=0, quantity=0, area_cm2=0,
		colours=0, sides=0, hours=0, decline_start_qty=0, decline_start_rate=0,
		decline_floor_qty=0, decline_floor_rate=0, cartons=0):
	"""Pure calculation for one Cost Driver against one job's measured
	values. Returns the computed cost for this driver alone."""
	tiers = tiers or []

	if measurement_basis in ("Per 1000 Sheets", "Per 1000 Pieces"):
		basis_qty = sheets_required if measurement_basis == "Per 1000 Sheets" else quantity
		effective_rate = _tier_rate(tiers, basis_qty) if is_tiered else rate
		return fixed_setup_cost + (basis_qty / 1000) * effective_rate

	if measurement_basis == "Per cm2":
		return fixed_setup_cost + area_cm2 * rate

	if measurement_basis == "Per Sheet":
		return fixed_setup_cost + sheets_required * rate

	if measurement_basis == "Per Sheet (Declining Rate)":
		effective_rate = _linear_decline_rate(
			sheets_required, decline_start_qty, decline_start_rate,
			decline_floor_qty, decline_floor_rate)
		return fixed_setup_cost + sheets_required * effective_rate

	if measurement_basis == "Per Carton":
		return fixed_setup_cost + cartons * rate

	if measurement_basis == "Per Side":
		return fixed_setup_cost + sides * rate

	if measurement_basis == "Per Colour":
		return fixed_setup_cost + colours * rate

	if measurement_basis == "Per Hour":
		return fixed_setup_cost + hours * rate

	if measurement_basis == "Flat Fee":
		return fixed_setup_cost + rate

	raise ValueError(f"Unknown measurement_basis: {measurement_basis}")


def compute_all_drivers(driver_configs, job_values):
	"""driver_configs: list of dicts, each the kwargs for one
	compute_cost_driver() call (minus the job_values, which are shared
	across all drivers for the same job). Returns (total, per_driver_dict)."""
	per_driver = {}
	total = 0.0
	for cfg in driver_configs:
		name = cfg["driver_name"]
		cost = compute_cost_driver(
			measurement_basis=cfg["measurement_basis"],
			fixed_setup_cost=cfg.get("fixed_setup_cost", 0),
			is_tiered=cfg.get("is_tiered", False),
			rate=cfg.get("rate", 0),
			tiers=cfg.get("tiers"),
			**job_values,
		)
		per_driver[name] = round(cost, 2)
		total += cost
	return round(total, 2), per_driver
