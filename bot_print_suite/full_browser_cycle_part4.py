import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

WO_NAME = "MFG-WO-2026-00002"
MT_NAME = "MAT-STE-2026-00002"


def run():
	# The draft transfer was timestamped BEFORE the opening stock
	# reconciliation (chronological stock ledger issue, not a real
	# shortage) - bump it to now before submitting.
	mt = frappe.get_doc("Stock Entry", MT_NAME)
	mt.set_posting_time = 1
	mt.posting_date = frappe.utils.nowdate()
	mt.posting_time = frappe.utils.nowtime()
	mt.save(ignore_permissions=True)
	mt.submit()
	print("MATERIAL_TRANSFER_SUBMITTED:", mt.name)

	mfg = frappe.get_doc(make_stock_entry(WO_NAME, "Manufacture"))
	for row in mfg.items:
		row.allow_zero_valuation_rate = 1
	mfg.insert(ignore_permissions=True)
	mfg.submit()
	print("MANUFACTURE_ENTRY_SUBMITTED:", mfg.name)

	wo = frappe.get_doc("Work Order", WO_NAME)
	print("WORK_ORDER_STATUS:", wo.status, "produced_qty:", wo.produced_qty)

	frappe.db.commit()
