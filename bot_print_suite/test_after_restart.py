import frappe
from frappe.handler import run_doc_method


def run():
	est = frappe.get_doc({
		"doctype": "Print Estimate",
		"customer": "Golden Arrow Printing & Packaging Co.",
		"product_template": "Folding Carton",
		"product_type": "Folding Carton",
		"finished_size_w": 510, "finished_size_h": 450,
		"quantity": 1000, "colours_front": 3, "colours_back": 0,
		"printing_method": "Sheetwise",
		"paper_type": "Ivory-350GSM",
		"sheet_size": "700x1000", "press": "Golden Arrow Offset",
		"margin_pct": 10,
	})
	est.insert(ignore_permissions=True)
	print("Inserted:", est.name, "| driver_costs_total:", est.driver_costs_total, "| rows:", len(est.applied_cost_drivers or []))

	# Now call apply_template via the EXACT mechanism the browser uses
	docs_json = frappe.as_json(est.as_dict())
	try:
		result = run_doc_method(docs=docs_json, method="apply_template")
		print("apply_template call SUCCEEDED:", result)
	except Exception as e:
		import traceback
		print("FAILED:", repr(e))
		traceback.print_exc()

	frappe.db.commit()
