import frappe
from frappe.model.workflow import apply_workflow
from bot_print_suite.utils import block_production_without_approved_artwork


def run():
	qtn = frappe.get_doc("Quotation", "SAL-QTN-2026-00002")  # already Approved from step 4 test
	print("QTN_STATUS:", qtn.docstatus, qtn.workflow_state)

	from erpnext.selling.doctype.quotation.quotation import make_sales_order
	so = make_sales_order(qtn.name)
	so.delivery_date = frappe.utils.add_days(frappe.utils.nowdate(), 30)
	so.naming_series = "GA-JOB-.YYYY.-.####"
	so.insert(ignore_permissions=True)
	so.submit()
	print("JOB_ORDER_CREATED:", so.name, "JOB_STATUS:", so.custom_job_status)

	# 1. No artwork yet -> production must be blocked
	fake_wo = frappe._dict(sales_order=so.name)
	try:
		block_production_without_approved_artwork(fake_wo)
		print("BLOCK_TEST_1: FAILED - should have thrown")
	except frappe.ValidationError as e:
		print("BLOCK_TEST_1_OK (blocked as expected):", str(e)[:80])

	# 2. Upload artwork, still Draft -> still blocked
	art = frappe.get_doc({"doctype": "Job Artwork", "sales_order": so.name, "version_no": 1})
	art.insert(ignore_permissions=True)
	try:
		block_production_without_approved_artwork(fake_wo)
		print("BLOCK_TEST_2: FAILED - should have thrown")
	except frappe.ValidationError as e:
		print("BLOCK_TEST_2_OK (blocked as expected):", str(e)[:80])

	# 3. Send to Customer -> Request Revision -> should auto-spawn v2, still blocked
	art = apply_workflow(art, "Send to Customer")
	art = apply_workflow(art, "Request Revision")
	v2_exists = frappe.db.exists("Job Artwork", {"sales_order": so.name, "version_no": 2})
	print("V2_AUTO_SPAWNED:", bool(v2_exists))

	# 4. Approve v2 -> production should now be allowed
	art2 = frappe.get_doc("Job Artwork", v2_exists)
	art2 = apply_workflow(art2, "Send to Customer")
	art2 = apply_workflow(art2, "Approve")
	block_production_without_approved_artwork(fake_wo)  # should NOT throw
	print("BLOCK_TEST_3_OK (no exception - production allowed after approval)")

	frappe.db.commit()
