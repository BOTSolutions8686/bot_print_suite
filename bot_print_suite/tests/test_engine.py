"""
Golden tests for the Print Estimation engine.

Per PLAN.md's Agent Rules: expected values are HAND-DERIVED (worked in
comments below), never asserted against the engine's own output. Run with:
	bench --site print-suite.local run-tests --app bot_print_suite
"""
import math
import unittest

from bot_print_suite.estimation.engine import (
	ups_per_sheet, paper_cost_per_sheet, compute_sheets_and_paper,
	compute_plates, compute_impressions, compute_press_run_cost,
	compute_ink_cost, compute_finishing_cost, calc_estimate,
)


class TestUpsPerSheet(unittest.TestCase):
	def test_90x55_card_on_700x1000_sheet(self):
		# Hand calc: item_w = 90 + 2*3 + 5 = 101, item_h = 55 + 2*3 + 5 = 66
		# usable_w = 700 - 2*10 = 680, usable_h = 1000 - 2*10 = 980
		# upright:  cols=floor(680/101)=6, rows=floor(980/66)=14  -> 84
		# rotated:  cols=floor(680/66)=10, rows=floor(980/101)=9  -> 90
		# max(84, 90) = 90
		item_w = 90 + 2 * 3 + 5
		item_h = 55 + 2 * 3 + 5
		result = ups_per_sheet(700, 1000, item_w, item_h, gripper_margin_mm=10)
		self.assertEqual(result, 90)


class TestPaperCost(unittest.TestCase):
	def test_700x1000_300gsm_at_3000_per_tonne(self):
		# area = 0.7m * 1.0m = 0.7 m2; weight = 0.7 * 300 / 1000 = 0.21 kg
		# rate/kg = 3000/1000 = 3 SAR/kg; cost = 0.21 * 3 = 0.63 SAR/sheet
		result = paper_cost_per_sheet(700, 1000, gsm=300, rate_per_tonne=3000)
		self.assertAlmostEqual(result, 0.63, places=4)

	def test_sheets_required_with_makeready_and_waste(self):
		# qty=10000, ups=90 -> base=ceil(10000/90)=112 (90*111=9990<10000)
		# waste = round(112 * 0.02) = round(2.24) = 2
		# sheets_required = 112 + 50 (makeready) + 2 = 164
		# paper_cost = 164 * 0.63 = 103.32
		sheets, cost = compute_sheets_and_paper(
			qty=10000, ups=90, makeready_sheets=50, run_waste_pct=2,
			sheet_w_mm=700, sheet_h_mm=1000, gsm=300, paper_rate_per_tonne=3000)
		self.assertEqual(sheets, 164)
		self.assertAlmostEqual(cost, 103.32, places=2)


class TestPlatesAndImpressions(unittest.TestCase):
	def test_sheetwise_plates_are_front_plus_back(self):
		# 4 front + 4 back, Sheetwise -> 8 plates (no shared set)
		self.assertEqual(compute_plates(4, 4, "Sheetwise"), 8)

	def test_work_and_turn_shares_one_plate_set(self):
		# Work and Turn: one shared plate set -> only front colour count
		self.assertEqual(compute_plates(4, 4, "Work and Turn"), 4)

	def test_impressions_double_sided_is_sheets_times_two(self):
		# 164 sheets, has back colours -> both sides printed -> 328 impressions
		# (true for BOTH Sheetwise and Work and Turn - W&T still passes the
		# sheet through twice, it just reuses one plate set, per PLAN.md)
		self.assertEqual(compute_impressions(164, 4, 4, "Sheetwise"), 328)
		self.assertEqual(compute_impressions(164, 4, 4, "Work and Turn"), 328)

	def test_impressions_single_sided_is_sheets_times_one(self):
		self.assertEqual(compute_impressions(164, 4, 0, "Sheetwise"), 164)


class TestPressRunAndInk(unittest.TestCase):
	def test_press_run_cost(self):
		# 500 makeready + (328/1000)*250 running = 500 + 82 = 582
		result = compute_press_run_cost(impressions=328, makeready_cost=500, running_rate_per_1000=250)
		self.assertAlmostEqual(result, 582, places=2)

	def test_ink_cost_medium_coverage(self):
		# 164 sheets * 0.7 m2 * 0.35 (medium) * 8 colours * 0.05 SAR/m2
		# = 114.8 * 0.35 = 40.18; *8 = 321.44; *0.05 = 16.072
		result = compute_ink_cost(
			sheets_required=164, sheet_w_mm=700, sheet_h_mm=1000,
			colours_front=4, colours_back=4, coverage_factor=0.35, ink_rate_per_sqm=0.05)
		self.assertAlmostEqual(result, 16.072, places=3)


class TestFinishingCost(unittest.TestCase):
	def test_mixed_unit_basis(self):
		# line1: Per 1000 Sheets @ 120 -> (164/1000)*120 = 19.68
		# line2: Per Sqm @ 2, sheet area 0.7 -> 164*0.7*2 = 229.6
		# total = 19.68 + 229.6 = 249.28
		total, per_line = compute_finishing_cost(
			[("Per 1000 Sheets", 120), ("Per Sqm", 2)],
			sheets_required=164, sheet_w_mm=700, sheet_h_mm=1000)
		self.assertAlmostEqual(total, 249.28, places=2)
		self.assertAlmostEqual(per_line[0], 19.68, places=2)
		self.assertAlmostEqual(per_line[1], 229.6, places=2)


class TestFullEstimateIntegration(unittest.TestCase):
	def test_end_to_end_90x55_card_10000_qty(self):
		# Composes every component above into one job:
		# 90x55mm card, qty 10000, 4+4 colour Sheetwise, 700x1000 sheet,
		# 300gsm @ 3000/tonne, medium ink coverage, press: makeready 500,
		# running 250/1000, gripper 10mm, waste 2%, makeready 50 sheets,
		# plate rate 45, one finishing line @ 120/1000 sheets + one @ 2/sqm,
		# die 50, freight 100, margin 20%.
		#
		# From the component tests above:
		#   ups=90, sheets_required=164, paper_cost=103.32
		#   plates(Sheetwise)=8 -> plate_cost = 8*45 = 360
		#   impressions=328 -> press_run_cost=582
		#   ink_cost=16.072
		#   finishing_cost_total=249.28
		# subtotal = 103.32+16.072+360+582+249.28+50+100 = 1460.672 -> 1460.67
		# sell_price = 1460.672 * 1.2 = 1752.8064 -> 1752.81
		result = calc_estimate(
			finished_w_mm=90, finished_h_mm=55, qty=10000,
			colours_front=4, colours_back=4, printing_method="Sheetwise",
			sheet_w_mm=700, sheet_h_mm=1000, gripper_margin_mm=10,
			bleed_mm=3, gutter_mm=5,
			makeready_sheets=50, run_waste_pct=2,
			makeready_cost=500, running_rate_per_1000=250,
			paper_rate_per_tonne=3000, gsm=300, plate_rate=45,
			coverage_factor=0.35, ink_rate_per_sqm=0.05,
			finishing_lines=[("Per 1000 Sheets", 120), ("Per Sqm", 2)],
			die_cost=50, freight_cost=100, margin_pct=20,
		)
		self.assertEqual(result["ups"], 90)
		self.assertEqual(result["sheets_required"], 164)
		self.assertAlmostEqual(result["paper_cost"], 103.32, places=2)
		self.assertAlmostEqual(result["plate_cost"], 360, places=2)
		self.assertAlmostEqual(result["press_run_cost"], 582, places=2)
		self.assertAlmostEqual(result["ink_cost"], 16.07, places=2)
		self.assertAlmostEqual(result["finishing_cost_total"], 249.28, places=2)
		self.assertAlmostEqual(result["subtotal"], 1460.67, places=2)
		self.assertAlmostEqual(result["sell_price"], 1752.81, places=2)

	def test_ups_override_bypasses_geometry_entirely(self):
		# Confirmed real (Talha, 2026-08-19, live with Mofeed): a 21x29.7cm
		# A4 flyer on a 70x100cm sheet computes 9-up geometrically (even
		# with a real gripper margin), but Mofeed's real practice is
		# 8-up - not fully explained by margins alone. ups_override=8
		# must be used as-is, with sheets_required recomputed from IT,
		# not from whatever geometry would have given.
		# qty=50000, ups=8 -> base=ceil(50000/8)=6250 (exact)
		# waste 0% (no press waste applied in this cut-down test), makeready 0
		# sheets_required = 6250
		result = calc_estimate(
			finished_w_mm=210, finished_h_mm=297, qty=50000,
			colours_front=4, colours_back=0, printing_method="Sheetwise",
			sheet_w_mm=700, sheet_h_mm=1000, gripper_margin_mm=10,
			bleed_mm=0, gutter_mm=0,
			makeready_sheets=0, run_waste_pct=0,
			makeready_cost=0, running_rate_per_1000=0,
			paper_rate_per_tonne=6000, gsm=150, plate_rate=37.5,
			coverage_factor=0.35, ink_rate_per_sqm=0,
			finishing_lines=[],
			die_cost=0, freight_cost=0, margin_pct=0,
			ups_override=8,
		)
		self.assertEqual(result["ups"], 8)
		self.assertEqual(result["sheets_required"], 6250)

	def test_confirmed_imposition_reference_beats_geometry(self):
		# The real fix for the 9-vs-8 gap: a confirmed reference for this
		# EXACT (sheet, finished-size) combination should be used instead
		# of geometry, with no per-job override needed. Same job as the
		# override test above, but via the general, reusable mechanism.
		references = [(700, 1000, 210, 297, 8, "Mofeed, 2026-08-19, matches published 8-up A4 standard")]
		result = calc_estimate(
			finished_w_mm=210, finished_h_mm=297, qty=50000,
			colours_front=4, colours_back=0, printing_method="Sheetwise",
			sheet_w_mm=700, sheet_h_mm=1000, gripper_margin_mm=10,
			bleed_mm=0, gutter_mm=0,
			makeready_sheets=0, run_waste_pct=0,
			makeready_cost=0, running_rate_per_1000=0,
			paper_rate_per_tonne=6000, gsm=150, plate_rate=37.5,
			coverage_factor=0.35, ink_rate_per_sqm=0,
			finishing_lines=[],
			die_cost=0, freight_cost=0, margin_pct=0,
			confirmed_ups_references=references,
		)
		self.assertEqual(result["ups"], 8)
		self.assertEqual(result["ups_source"], "confirmed")
		self.assertEqual(result["sheets_required"], 6250)

	def test_confirmed_imposition_reference_matches_rotated_orientation(self):
		# A finished size given as 297x210 is the same physical piece as
		# 210x297 - the reference must match either way round.
		references = [(700, 1000, 210, 297, 8, "test")]
		result = calc_estimate(
			finished_w_mm=297, finished_h_mm=210, qty=50000,
			colours_front=4, colours_back=0, printing_method="Sheetwise",
			sheet_w_mm=700, sheet_h_mm=1000, gripper_margin_mm=10,
			bleed_mm=0, gutter_mm=0,
			makeready_sheets=0, run_waste_pct=0,
			makeready_cost=0, running_rate_per_1000=0,
			paper_rate_per_tonne=6000, gsm=150, plate_rate=37.5,
			coverage_factor=0.35, ink_rate_per_sqm=0,
			finishing_lines=[],
			die_cost=0, freight_cost=0, margin_pct=0,
			confirmed_ups_references=references,
		)
		self.assertEqual(result["ups"], 8)
		self.assertEqual(result["ups_source"], "confirmed")

	def test_no_confirmed_reference_falls_back_to_geometry(self):
		# An unmatched sheet/size combination must NOT be affected by
		# unrelated confirmed references - falls through to geometry,
		# same as if no references existed at all.
		references = [(700, 1000, 210, 297, 8, "test - unrelated size")]
		result = calc_estimate(
			finished_w_mm=100, finished_h_mm=150, qty=1000,
			colours_front=4, colours_back=0, printing_method="Sheetwise",
			sheet_w_mm=700, sheet_h_mm=1000, gripper_margin_mm=10,
			bleed_mm=0, gutter_mm=0,
			makeready_sheets=0, run_waste_pct=0,
			makeready_cost=0, running_rate_per_1000=0,
			paper_rate_per_tonne=6000, gsm=150, plate_rate=37.5,
			coverage_factor=0.35, ink_rate_per_sqm=0,
			finishing_lines=[],
			die_cost=0, freight_cost=0, margin_pct=0,
			confirmed_ups_references=references,
		)
		self.assertEqual(result["ups_source"], "geometry")

	def test_explicit_override_beats_confirmed_reference(self):
		# Priority order: a specific per-job override (a documented reason
		# for THIS job) must win over a general confirmed reference, not
		# the other way round.
		references = [(700, 1000, 210, 297, 8, "test")]
		result = calc_estimate(
			finished_w_mm=210, finished_h_mm=297, qty=50000,
			colours_front=4, colours_back=0, printing_method="Sheetwise",
			sheet_w_mm=700, sheet_h_mm=1000, gripper_margin_mm=10,
			bleed_mm=0, gutter_mm=0,
			makeready_sheets=0, run_waste_pct=0,
			makeready_cost=0, running_rate_per_1000=0,
			paper_rate_per_tonne=6000, gsm=150, plate_rate=37.5,
			coverage_factor=0.35, ink_rate_per_sqm=0,
			finishing_lines=[],
			die_cost=0, freight_cost=0, margin_pct=0,
			ups_override=6, confirmed_ups_references=references,
		)
		self.assertEqual(result["ups"], 6)
		self.assertEqual(result["ups_source"], "override")


if __name__ == "__main__":
	unittest.main()
