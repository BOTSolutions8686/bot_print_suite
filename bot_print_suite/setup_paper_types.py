import frappe


def run():
	if not frappe.db.exists("Paper Type", "Ivory-350.0GSM"):
		frappe.get_doc({
			"doctype": "Paper Type",
			"paper_name": "Ivory", "gsm": 350,
			"rate_per_tonne": 5500,
			"reems_per_tonne": 40.8, "sheets_per_reem": 100,
			"notes": "Confirmed directly by Mofeed (Golden Arrow's estimator). "
				"Verified: reproduced his real 810 SAR paper cost for a "
				"1,000-piece box job to within 0.2%. See PLAN.md Step 10.",
		}).insert(ignore_permissions=True)
		frappe.db.commit()
		print("PAPER_TYPE_CREATED")
	else:
		print("PAPER_TYPE_EXISTS")

	pt = frappe.get_doc("Paper Type", "Ivory-350.0GSM")
	print("sheets_per_tonne:", pt.sheets_per_tonne, "cost_per_sheet:", pt.cost_per_sheet)
