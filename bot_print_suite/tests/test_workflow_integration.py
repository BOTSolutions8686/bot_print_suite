"""Database-backed coverage for the complete print job document chain."""

import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from bot_print_suite.production.start_production import start_production
from erpnext.selling.doctype.quotation.quotation import make_sales_order


class TestPrintWorkflowIntegration(IntegrationTestCase):
	def test_enquiry_to_production_chain(self):
		"""Every hand-off uses the real DocTypes, hooks and ERPNext mapper."""
		frappe.set_user("Administrator")
		suffix = frappe.generate_hash(length=8)

		enquiry = frappe.get_doc({
			"doctype": "Print Enquiry",
			"customer_name_new": f"Workflow Test Customer {suffix}",
			"contact_name": "Integration Test",
			"phone": "+966500000000",
			"source": "Portal",
			"product_type": "Folding Carton",
			"requested_quantity": 1000,
			"rough_spec": "Automated full-chain regression test",
		}).insert()

		estimate_name = enquiry.make_print_estimate()
		estimate = frappe.get_doc("Print Estimate", estimate_name)
		estimate.update({
			"finished_width_cm": 20,
			"finished_height_cm": 10,
			"quantity": 1000,
			"colours_front": 4,
			"paper_type": "Ivory-350GSM",
			"substrate": "Ivory",
			"gsm": 350,
			"sheet_size": "70x100",
			"press": "Heidelberg SM74",
			"die_width_cm": 20,
			"die_height_cm": 10,
			"die_requirement": "New die required",
		})
		estimate.save()
		self.assertGreater(estimate.sell_price, 0)
		self.assertGreater(estimate.sheets_required, 0)
		self.assertEqual(estimate.glue_sides, 1)
		self.assertTrue(any(
			row.enabled and "glue" in row.cost_driver.lower()
			for row in estimate.applied_cost_drivers
		))

		# The simple finishing controls must drive the real estimate, not
		# merely record labels that disagree with the Cost Items table.
		die_row = next(row for row in estimate.applied_cost_drivers
			if "die" in row.cost_driver.lower() or "frame" in row.cost_driver.lower())
		glue_row = next(row for row in estimate.applied_cost_drivers
			if "glue" in row.cost_driver.lower())
		original_die_cost = die_row.computed_cost
		original_glue_cost = glue_row.computed_cost
		original_subtotal = estimate.subtotal

		estimate.die_requirement = "Use existing die"
		estimate.save()
		die_row = next(row for row in estimate.applied_cost_drivers
			if "die" in row.cost_driver.lower() or "frame" in row.cost_driver.lower())
		self.assertEqual(die_row.computed_cost, 0)
		self.assertAlmostEqual(estimate.subtotal, original_subtotal - original_die_cost, places=2)

		estimate.die_requirement = "New die required"
		estimate.save()
		die_row = next(row for row in estimate.applied_cost_drivers
			if "die" in row.cost_driver.lower() or "frame" in row.cost_driver.lower())
		self.assertAlmostEqual(die_row.computed_cost, original_die_cost, places=2)

		estimate.glue_sides = 0
		estimate.save()
		glue_row = next(row for row in estimate.applied_cost_drivers
			if "glue" in row.cost_driver.lower())
		self.assertFalse(glue_row.enabled)
		self.assertEqual(glue_row.computed_cost, 0)
		self.assertAlmostEqual(estimate.subtotal, original_subtotal - original_glue_cost, places=2)

		estimate.glue_sides = 1
		estimate.save()
		glue_row = next(row for row in estimate.applied_cost_drivers
			if "glue" in row.cost_driver.lower())
		self.assertTrue(glue_row.enabled)
		self.assertAlmostEqual(glue_row.computed_cost, original_glue_cost, places=2)

		# No unverified multi-side formula: a confirmed total is required
		# through the same native row override available to estimators.
		estimate.glue_sides = 2
		with self.assertRaises(frappe.ValidationError):
			estimate.save()
		estimate.reload()
		estimate.glue_sides = 2
		estimate.multi_side_glue_cost = original_glue_cost + 100
		estimate.save()
		glue_row = next(row for row in estimate.applied_cost_drivers
			if "glue" in row.cost_driver.lower())
		self.assertTrue(glue_row.cost_override_enabled)
		self.assertAlmostEqual(glue_row.computed_cost, original_glue_cost + 100, places=2)

		# Restore the ordinary verified one-side case before continuing the
		# quotation-to-production workflow below.
		estimate.glue_sides = 1
		estimate.save()
		glue_row = next(row for row in estimate.applied_cost_drivers
			if "glue" in row.cost_driver.lower())
		self.assertFalse(glue_row.cost_override_enabled)
		self.assertEqual(estimate.multi_side_glue_cost, 0)

		quotation_name = estimate.create_quotation()
		quotation = frappe.get_doc("Quotation", quotation_name)
		quotation = apply_workflow(quotation, "Submit for Approval")
		quotation = apply_workflow(quotation, "Approve")
		quotation.reload()
		self.assertEqual(quotation.docstatus, 1)
		self.assertEqual(quotation.custom_print_estimate, estimate.name)
		# ERPNext stores the per-unit Currency rate at site precision, so a
		# batch total can differ by a few halalas after qty × rounded rate.
		self.assertAlmostEqual(quotation.grand_total, estimate.sell_price, delta=1)
		self.assertTrue(quotation.items[0].item_code.startswith("JOB-"))
		self.assertFalse(quotation.items[0].item_code.startswith("PRINT-JOB-"))

		sales_order = make_sales_order(quotation.name)
		sales_order.delivery_date = add_days(nowdate(), 7)
		sales_order.insert()
		sales_order.submit()
		self.assertEqual(sales_order.items[0].item_code, quotation.items[0].item_code)
		self.assertEqual(sales_order.items[0].prevdoc_docname, quotation.name)
		self.assertAlmostEqual(sales_order.grand_total, quotation.grand_total, places=2)

		with self.assertRaises(frappe.ValidationError):
			start_production(sales_order.name)

		artwork = frappe.get_doc({
			"doctype": "Job Artwork",
			"sales_order": sales_order.name,
			"version_no": 1,
			"artwork_file": "/private/files/test-artwork.pdf",
		}).insert()
		artwork = apply_workflow(artwork, "Send to Customer")
		artwork = apply_workflow(artwork, "Approve")
		self.assertEqual(artwork.status, "Approved")

		production = start_production(sales_order.name)
		production_again = start_production(sales_order.name)
		self.assertTrue(production_again["already_started"])
		self.assertEqual(production_again["work_order"], production["work_order"])
		self.assertEqual(
			production_again["material_transfer"], production["material_transfer"]
		)
		work_order = frappe.get_doc("Work Order", production["work_order"])
		material_transfer = frappe.get_doc("Stock Entry", production["material_transfer"])
		bom = frappe.get_doc("BOM", work_order.bom_no)

		self.assertEqual(work_order.docstatus, 1)
		self.assertEqual(work_order.sales_order, sales_order.name)
		self.assertEqual(work_order.production_item, sales_order.items[0].item_code)
		self.assertEqual(bom.item, sales_order.items[0].item_code)
		self.assertEqual(material_transfer.docstatus, 0)
		self.assertEqual(material_transfer.work_order, work_order.name)
		sales_order.reload()
		self.assertEqual(sales_order.items[0].item_code, quotation.items[0].item_code)
