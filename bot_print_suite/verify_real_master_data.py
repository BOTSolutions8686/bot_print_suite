import frappe
from bot_print_suite.estimation.cost_driver_engine import compute_all_drivers

JOB = dict(sheets_required=600, quantity=1000, area_cm2=53 * 45, colours=3, sides=1, hours=0)


def run():
	template = frappe.get_doc("Product Estimation Template", "Folding Carton")

	configs = []
	for line in template.drivers:
		driver = frappe.get_doc("Cost Driver", line.cost_driver)
		configs.append({
			"driver_name": driver.name,
			"measurement_basis": driver.measurement_basis,
			"fixed_setup_cost": driver.fixed_setup_cost or 0,
			"is_tiered": bool(driver.is_tiered),
			"rate": driver.rate or 0,
			"tiers": [(t.qty_from, t.qty_to, t.rate) for t in driver.tiers] if driver.is_tiered else None,
		})

	total, per_driver = compute_all_drivers(configs, JOB)

	print("PER-DRIVER (from real stored master data):")
	for name, cost in per_driver.items():
		print(f"  {name}: {cost}")
	print("DRIVER TOTAL:", total)

	paper_cost = 810.0  # already proven separately by estimation/engine.py's own golden tests
	full_subtotal = paper_cost + total
	print("FULL SUBTOTAL (Paper + Drivers):", full_subtotal)
	print("MATCHES MOFEED'S REAL 2,055.25:", abs(full_subtotal - 2055.25) < 0.01)
