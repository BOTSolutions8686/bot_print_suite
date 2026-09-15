import frappe

# Every rate here is Mofeed's own confirmed number (Golden Arrow's
# estimator), verified against his real quoted job before being trusted -
# see PLAN.md Step 10 for the full derivation of each one.

DRIVERS = [
	{
		"driver_name": "Plate", "measurement_basis": "Per Colour",
		"rate": 37.5,
		"notes": "Confirmed directly by Mofeed: 37.5 SAR per colour.",
	},
	{
		"driver_name": "Printing", "measurement_basis": "Per 1000 Sheets",
		"fixed_setup_cost": 100, "is_tiered": 1,
		"tiers": [
			{"qty_from": 0, "qty_to": 1000, "rate": 500},
			{"qty_from": 1001, "qty_to": 5000, "rate": 180},
			{"qty_from": 5001, "qty_to": 10000, "rate": 140},
			{"qty_from": 10001, "qty_to": 999999, "rate": 100},
		],
		"notes": "Tier table confirmed directly by Mofeed. The 100 SAR "
			"fixed setup cost was reverse-engineered to make the tiers "
			"match his real quoted 400 SAR for a 600-sheet job (100 + "
			"600/1000*500 = 400, exact). Pending: his answer for the "
			"same job at 3,000 pieces, to confirm beyond one data point.",
	},
	{
		"driver_name": "Die / Frame", "measurement_basis": "Per cm2",
		"rate": 0.15,
		"notes": "Mofeed's own words: '15 halala per centimetre' - only "
			"matches his real quoted ~360 SAR as an AREA rate (die "
			"53x45cm = 2385 cm2 x 0.15 = 357.75), not a linear one. "
			"Confirmed by testing both interpretations against his real "
			"number.",
	},
	{
		"driver_name": "Cutting", "measurement_basis": "Per 1000 Pieces",
		"rate": 150,
		"notes": "150 SAR per 1000 pieces confirmed for this job. "
			"Confirmed to also scale down with volume like Printing, but "
			"the real tier table is still unconfirmed - flat for now.",
	},
	{
		"driver_name": "Glue - 1 Side", "measurement_basis": "Flat Fee",
		"rate": 150,
		"notes": "150 SAR confirmed for this job (1-side gluing). "
			"Confirmed to scale with side count and volume, but the real "
			"rate table is still unconfirmed - flat for now.",
	},
	{
		"driver_name": "Artwork", "measurement_basis": "Flat Fee",
		"rate": 25,
		"notes": "Flat 25 SAR lump sum, confirmed unconditional.",
	},
	{
		"driver_name": "Packing", "measurement_basis": "Flat Fee",
		"rate": 50,
		"notes": "Flat 50 SAR, confirmed. Was mislabelled 'Rolling' in "
			"an earlier misread of Mofeed's handwriting - corrected "
			"directly by Talha.",
	},
]


def run():
	for d in DRIVERS:
		if frappe.db.exists("Cost Driver", d["driver_name"]):
			continue
		tiers = d.pop("tiers", None)
		doc = frappe.get_doc({"doctype": "Cost Driver", **d})
		if tiers:
			for t in tiers:
				doc.append("tiers", t)
		doc.insert(ignore_permissions=True)
		print("CREATED:", doc.name)

	if not frappe.db.exists("Product Estimation Template", "Folding Carton"):
		template = frappe.get_doc({
			"doctype": "Product Estimation Template",
			"template_name": "Folding Carton",
			"product_type": "Folding Carton",
			"notes": "Built and verified against Mofeed's real confirmed "
				"job (1,000 pieces) - see PLAN.md Step 10.",
			"drivers": [
				{"cost_driver": "Plate", "required": 1, "default_enabled": 1},
				{"cost_driver": "Printing", "required": 1, "default_enabled": 1},
				{"cost_driver": "Die / Frame", "required": 1, "default_enabled": 1},
				{"cost_driver": "Cutting", "required": 1, "default_enabled": 1},
				{"cost_driver": "Glue - 1 Side", "required": 0, "default_enabled": 1},
				{"cost_driver": "Artwork", "required": 0, "default_enabled": 1},
				{"cost_driver": "Packing", "required": 0, "default_enabled": 1},
			],
		})
		template.insert(ignore_permissions=True)
		print("CREATED: Folding Carton template")

	frappe.db.commit()
