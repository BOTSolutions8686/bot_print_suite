import frappe
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

SO_NAME = "GA-JOB-2026-0002"


def run():
	dn = make_delivery_note(SO_NAME)
	for row in dn.items:
		row.allow_zero_valuation_rate = 1
		row.warehouse = "Finished Goods - GAP"
	dn.insert(ignore_permissions=True)
	dn.submit()
	print("DELIVERY_NOTE_SUBMITTED:", dn.name)

	frappe.db.set_value("Sales Order", SO_NAME, "custom_job_status", "Delivered")

	si = make_sales_invoice(dn.name)
	si.insert(ignore_permissions=True)
	si.submit()
	print("SALES_INVOICE_SUBMITTED:", si.name, "grand_total:", si.grand_total)

	so = frappe.get_doc("Sales Order", SO_NAME)
	print("FINAL_SO_STATUS:", so.status, "job_status:", so.custom_job_status)

	frappe.db.commit()
