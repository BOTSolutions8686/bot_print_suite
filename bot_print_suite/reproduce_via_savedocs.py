import frappe
import json
from frappe.desk.form.save import savedocs

def run():
	doc_json = '{"docstatus":0,"doctype":"Print Estimate","name":"new-print-estimate-dgdhtjjwdu","__islocal":1,"__unsaved":1,"owner":"Administrator","product_type":"Folding Carton","colours_back":0,"printing_method":"Sheetwise","ink_coverage":"Medium","finishing_operations":[],"bleed_mm":3,"gutter_mm":5,"quantity_breaks":[],"computed_breaks":[],"glue_sides":0,"applied_cost_drivers":[],"margin_pct":"20","customer":"Golden Arrow Printing & Packaging Co.","finished_size_w":510,"finished_size_h":450,"quantity":1000,"product_template":"Folding Carton","colours_front":3,"substrate":"Ivory","gsm":350,"paper_type":"Ivory-350GSM","sheet_size":"700x1000","press":"Golden Arrow Offset"}'
	try:
		savedocs(doc=doc_json, action="Save")
		print("SUCCESS via savedocs()")
	except Exception as e:
		import traceback
		print("FAILED:", repr(e))
		traceback.print_exc()
	frappe.db.commit()
