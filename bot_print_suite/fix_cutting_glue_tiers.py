import frappe

TIERS = [
	{"qty_from": 0, "qty_to": 1000, "rate": 100},
	{"qty_from": 1001, "qty_to": 5000, "rate": 60},
	{"qty_from": 5001, "qty_to": 10000, "rate": 50},
	{"qty_from": 10001, "qty_to": 50000, "rate": 39},
	{"qty_from": 50001, "qty_to": 999999, "rate": 29.5},
]

NOTE = ("Confirmed by Talha with 5 real data points (1,000/5,000/10,000/"
	"50,000/100,000 pieces = 150/350/550/2,000/3,000 SAR). Fixed 50 SAR "
	"+ tiered rate exactly reproduces all 5 points. Same table used for "
	"BOTH Cutting and Glue (Mofeed's own statement - identical pricing "
	"structure for both). Glue's 'extra per side' rule is STILL UNCONFIRMED "
	"- Talha described '10 SAR per side per 1000' but that doesn't "
	"reproduce his own worked example (2-side, 5000pcs = 600 SAR) - "
	"working backward suggests the real per-side rate is closer to 50, "
	"not 10. Left as single-side pricing only until clarified - do NOT "
	"apply a side multiplier without confirming the real formula.")


def run():
	for name in ["Cutting", "Glue - 1 Side"]:
		driver = frappe.get_doc("Cost Driver", name)
		driver.measurement_basis = "Per 1000 Pieces"
		driver.fixed_setup_cost = 50
		driver.is_tiered = 1
		driver.rate = 0
		driver.tiers = []
		for t in TIERS:
			driver.append("tiers", t)
		driver.notes = NOTE
		driver.save(ignore_permissions=True)
		print(f"Updated {name}")

	frappe.db.commit()
	# Verify all 5 points for both drivers
	from bot_print_suite.estimation.cost_driver_engine import compute_cost_driver
	tiers_tuples = [(t["qty_from"], t["qty_to"], t["rate"]) for t in TIERS]
	for qty in [1000, 5000, 10000, 50000, 100000]:
		cost = compute_cost_driver(measurement_basis="Per 1000 Pieces", fixed_setup_cost=50,
			is_tiered=True, tiers=tiers_tuples, quantity=qty)
		print(f"  qty={qty}: {cost}")
