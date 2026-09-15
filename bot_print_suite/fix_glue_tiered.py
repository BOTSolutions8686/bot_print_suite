import frappe


def run():
	glue = frappe.get_doc("Cost Driver", "Glue - 1 Side")
	glue.measurement_basis = "Per 1000 Pieces"
	glue.fixed_setup_cost = 50
	glue.is_tiered = 1
	glue.rate = 0  # unused now that it's tiered
	glue.tiers = []
	glue.append("tiers", {"qty_from": 0, "qty_to": 1000, "rate": 100})
	glue.append("tiers", {"qty_from": 1001, "qty_to": 999999, "rate": 50})
	glue.notes = ("CORRECTED: was wrongly modelled as flat 150 SAR/side "
		"(Per Side), which had zero real basis beyond the single 1,000-"
		"piece data point. Confirmed via Talha with a second real data "
		"point (10,000 pieces = 550 SAR): fixed 50 + tiered rate "
		"(100/1000 at <=1,000 pieces, 50/1000 above) - same shape as "
		"Printing's real formula. Verifies exactly against both known "
		"points: 50+1*100=150 (1,000pcs), 50+10*50=550 (10,000pcs). "
		"'Number of sides' is currently NOT priced separately - only "
		"one side's real rate is confirmed. If 2-side gluing genuinely "
		"costs more, we don't have real data for that yet.")
	glue.save(ignore_permissions=True)
	print("Updated. Verify: 1000pcs =", 50 + 1*100, "| 10000pcs =", 50 + 10*50)
	frappe.db.commit()
