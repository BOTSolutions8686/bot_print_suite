"""
Golden tests for the Cost Driver engine, against Mofeed's REAL confirmed
numbers (Golden Arrow's estimator) - not invented numbers. Per PLAN.md's
own agent rule: expected values are HAND-DERIVED and checked against
what he actually told Talha, never asserted against the engine's own
output.

The job throughout: 1,000 folding cartons, 3 colours front, 1-side glue,
die 53x45cm, 600 sheets required (already computed by the existing
geometry engine, not re-derived here).
"""
import unittest
from bot_print_suite.estimation.cost_driver_engine import compute_cost_driver, compute_all_drivers, compute_cartons

JOB = dict(sheets_required=600, quantity=1000, area_cm2=53 * 45, colours=3, sides=1, hours=0)


class TestIndividualDrivers(unittest.TestCase):
	def test_plate_per_colour(self):
		# Mofeed confirmed directly: 37.5 SAR per colour. 3 colours.
		cost = compute_cost_driver(measurement_basis="Per Colour", rate=37.5, **JOB)
		self.assertAlmostEqual(cost, 112.5, places=2)

	def test_die_per_cm2(self):
		# 0.15 SAR/cm^2 x (53 x 45 = 2385 cm^2) = 357.75
		# Matches his real quoted ~360 SAR closely - the 0.15 rate itself
		# came from testing this exact formula against his real number.
		cost = compute_cost_driver(measurement_basis="Per cm2", rate=0.15, **JOB)
		self.assertAlmostEqual(cost, 357.75, places=2)

	def test_die_per_cm2_uses_full_sheet_area_not_ups_footprint(self):
		# Corrected real physics (Talha, 2026-08-19, live with Mofeed):
		# a die/frame is cut against the FULL press sheet, not just the
		# footprint of the pieces actually extracted - whatever's left
		# on the sheet after pulling the ups is wasted, so the whole
		# sheet's area is what gets charged. Verified exactly: 70x100cm
		# sheet = 7,000 cm² x 0.15 SAR/cm² = 1,050.00 SAR, matching
		# Mofeed's real number for a 48x33cm/4-up job on that sheet -
		# NOT the old (48x33=1,584cm² x 4 ups = 6,336cm²) x 0.15 = 950.40,
		# which undercounts whenever the ups don't perfectly tile the
		# sheet.
		full_sheet_area_cm2 = 70 * 100
		job = dict(JOB, area_cm2=full_sheet_area_cm2)
		cost = compute_cost_driver(measurement_basis="Per cm2", rate=0.15, **job)
		self.assertAlmostEqual(cost, 1050.0, places=2)

	def test_printing_fixed_plus_tiered(self):
		# The real, reverse-engineered shape: a 100 SAR fixed setup cost
		# PLUS his own confirmed tier table (500/1000 at <=1000 sheets).
		# 600 sheets falls in the first tier (rate 500) ->
		# 100 + (600/1000)*500 = 100 + 300 = 400 - matches his real
		# quoted number for this job exactly.
		tiers = [(0, 1000, 500), (1001, 5000, 180), (5001, 10000, 140), (10001, 999999, 100)]
		cost = compute_cost_driver(
			measurement_basis="Per 1000 Sheets", fixed_setup_cost=100,
			is_tiered=True, tiers=tiers, **JOB)
		self.assertAlmostEqual(cost, 400.0, places=2)

	def test_cutting_per_1000_pieces(self):
		# 150 SAR per 1000 pieces, flat for now (his real tier table for
		# Cutting is still unconfirmed - this is the single-rate case).
		cost = compute_cost_driver(measurement_basis="Per 1000 Pieces", rate=150, **JOB)
		self.assertAlmostEqual(cost, 150.0, places=2)

	def test_glue_flat_for_this_job(self):
		# 150 SAR flat, 1-side gluing - his real per-side/per-volume rate
		# table is still unconfirmed, so modelled as flat for this job.
		cost = compute_cost_driver(measurement_basis="Flat Fee", rate=150, **JOB)
		self.assertAlmostEqual(cost, 150.0, places=2)

	def test_artwork_flat(self):
		cost = compute_cost_driver(measurement_basis="Flat Fee", rate=25, **JOB)
		self.assertAlmostEqual(cost, 25.0, places=2)

	def test_packing_flat(self):
		cost = compute_cost_driver(measurement_basis="Flat Fee", rate=50, **JOB)
		self.assertAlmostEqual(cost, 50.0, places=2)

	def test_lamination_declining_rate_at_start_point(self):
		# Mofeed's real confirmed low-volume point: 0.80 SAR/sheet at
		# 1,000 sheets exactly. 600 sheets (this job's real
		# sheets_required) is BELOW the confirmed start point, so the
		# starting rate applies as-is, no interpolation below it.
		cost = compute_cost_driver(measurement_basis="Per Sheet (Declining Rate)",
			decline_start_qty=1000, decline_start_rate=0.80,
			decline_floor_qty=150000, decline_floor_rate=0.55, **JOB)
		self.assertAlmostEqual(cost, 600 * 0.80, places=2)

	def test_lamination_declining_rate_at_floor_point(self):
		# Mofeed's real confirmed floor: 0.55 SAR/sheet at 150,000
		# sheets and beyond.
		job = dict(JOB, sheets_required=150000)
		cost = compute_cost_driver(measurement_basis="Per Sheet (Declining Rate)",
			decline_start_qty=1000, decline_start_rate=0.80,
			decline_floor_qty=150000, decline_floor_rate=0.55, **job)
		self.assertAlmostEqual(cost, 150000 * 0.55, places=2)

	def test_lamination_declining_rate_midpoint_interpolates(self):
		# Halfway between the two confirmed sheet counts should land
		# halfway between the two confirmed rates - the whole point of
		# using linear interpolation instead of inventing a tier table.
		mid_qty = (1000 + 150000) / 2
		job = dict(JOB, sheets_required=mid_qty)
		cost = compute_cost_driver(measurement_basis="Per Sheet (Declining Rate)",
			decline_start_qty=1000, decline_start_rate=0.80,
			decline_floor_qty=150000, decline_floor_rate=0.55, **job)
		expected_rate = (0.80 + 0.55) / 2
		self.assertAlmostEqual(cost, mid_qty * expected_rate, places=2)

	def test_packing_cartons_reproduces_mofeeds_real_example(self):
		# Mofeed's real worked example (Talha, 2026-08-19): 125,000
		# sheets on a 70x100 sheet (8 A4-equivalents/sheet), 300gsm
		# stock, 3000 normalized-sheets-per-carton convention.
		# 125,000 x 8 x (300/100) = 3,000,000 -> /3000 = 1,000 cartons
		# exactly - his real number, not rounded.
		cartons = compute_cartons(sheets_required=125000, a4_equivalent_count=8,
			gsm=300, sheets_per_carton=3000)
		self.assertAlmostEqual(cartons, 1000.0, places=4)

	def test_packing_per_carton_basis_reproduces_mofeeds_real_cost(self):
		# Same real example, full cost: 1,000 cartons x 1.4 SAR/carton
		# = 1,400 SAR - matches Mofeed's real number exactly.
		job = dict(JOB, sheets_required=125000)
		cartons = compute_cartons(sheets_required=125000, a4_equivalent_count=8,
			gsm=300, sheets_per_carton=3000)
		cost = compute_cost_driver(measurement_basis="Per Carton", rate=1.4, cartons=cartons, **job)
		self.assertAlmostEqual(cost, 1400.0, places=2)

	def test_glue_new_tiered_per_1000_pieces(self):
		# Mofeed's real tier table (Talha, 2026-08-19), corrected after
		# an initial mistranscription (his message repeated '10000' for
		# two different tiers, initially misread as a 30/1000 ceiling
		# with no bound). Real table, no fixed setup cost: 150/1000 up
		# to 1,000pcs, 80/1000 to 5,000, 55/1000 to 10,000, 40/1000 to
		# 50,000, 30/1000 to 150,000, 25/1000 above that. Verified
		# exactly against this job's real quantity (500,000pcs, top
		# tier): (500000/1000)*25 = 12,500, matching Mofeed's real
		# number for this job exactly.
		tiers = [(0, 1000, 150), (1001, 5000, 80), (5001, 10000, 55),
			(10001, 50000, 40), (50001, 150000, 30), (150001, 999999999, 25)]
		job = dict(JOB, quantity=500000)
		cost = compute_cost_driver(measurement_basis="Per 1000 Pieces",
			is_tiered=True, tiers=tiers, **job)
		self.assertAlmostEqual(cost, 12500.0, places=2)


class TestFullJobReconciliation(unittest.TestCase):
	def test_reproduces_mofeeds_real_subtotal(self):
		"""THE acceptance test agreed with Talha before extending this
		design to any other product type: does the generic Cost Driver
		engine reproduce Mofeed's real confirmed job, using only his own
		confirmed rules? Paper (810 SAR) is NOT included here - it stays
		in the existing geometry engine (estimation/engine.py), already
		proven correct by its own golden tests. This test covers
		everything ELSE: Plate, Printing, Die, Cutting, Glue, Artwork,
		Packing.

		Hand-derived sum: 112.5 + 400 + 357.75 + 150 + 150 + 25 + 50
		= 1,245.25

		Full job subtotal = Paper (810, proven separately) + this
		(1,245.25) = 2,055.25 SAR - matching what Mofeed told Talha
		directly ("2.2 or something" per piece before margin/VAT).
		"""
		configs = [
			{"driver_name": "Plate", "measurement_basis": "Per Colour", "rate": 37.5},
			{"driver_name": "Printing", "measurement_basis": "Per 1000 Sheets",
			 "fixed_setup_cost": 100, "is_tiered": True,
			 "tiers": [(0, 1000, 500), (1001, 5000, 180), (5001, 10000, 140), (10001, 999999, 100)]},
			{"driver_name": "Die", "measurement_basis": "Per cm2", "rate": 0.15},
			{"driver_name": "Cutting", "measurement_basis": "Per 1000 Pieces", "rate": 150},
			{"driver_name": "Glue", "measurement_basis": "Flat Fee", "rate": 150},
			{"driver_name": "Artwork", "measurement_basis": "Flat Fee", "rate": 25},
			{"driver_name": "Packing", "measurement_basis": "Flat Fee", "rate": 50},
		]

		total, per_driver = compute_all_drivers(configs, JOB)

		self.assertAlmostEqual(per_driver["Plate"], 112.5, places=2)
		self.assertAlmostEqual(per_driver["Printing"], 400.0, places=2)
		self.assertAlmostEqual(per_driver["Die"], 357.75, places=2)
		self.assertAlmostEqual(per_driver["Cutting"], 150.0, places=2)
		self.assertAlmostEqual(per_driver["Glue"], 150.0, places=2)
		self.assertAlmostEqual(per_driver["Artwork"], 25.0, places=2)
		self.assertAlmostEqual(per_driver["Packing"], 50.0, places=2)
		self.assertAlmostEqual(total, 1245.25, places=2)

		PAPER_COST_ALREADY_PROVEN = 810.0
		full_job_subtotal = PAPER_COST_ALREADY_PROVEN + total
		self.assertAlmostEqual(full_job_subtotal, 2055.25, places=2)


if __name__ == "__main__":
	unittest.main()
