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

		# Multi-side glue uses the normal tiered one-side result multiplied
		# by sides. The native row override remains available for exceptions.
		estimate.glue_sides = 2
		estimate.save()
		glue_row = next(row for row in estimate.applied_cost_drivers
			if "glue" in row.cost_driver.lower())
		self.assertFalse(glue_row.cost_override_enabled)
		self.assertAlmostEqual(glue_row.computed_cost, original_glue_cost * 2, places=2)

		glue_row.cost_override_enabled = 1
		glue_row.cost_override = original_glue_cost + 100
		glue_row.override_reason = "Confirmed exception to normal side multiplier"
		estimate.save()
		self.assertAlmostEqual(glue_row.computed_cost, original_glue_cost + 100, places=2)

		# Restore the ordinary verified one-side case before continuing the
		# quotation-to-production workflow below.
		estimate.glue_sides = 1
		glue_row.cost_override_enabled = 0
		glue_row.cost_override = 0
		glue_row.override_reason = None
		estimate.save()
		glue_row = next(row for row in estimate.applied_cost_drivers
			if "glue" in row.cost_driver.lower())
		self.assertFalse(glue_row.cost_override_enabled)

		# The convenient checkbox and native Lamination row work in both
		# directions and feed the actual estimate total.
		lamination_row = next(row for row in estimate.applied_cost_drivers
			if "lamination" in row.cost_driver.lower())
		self.assertFalse(estimate.lamination_required)
		self.assertFalse(lamination_row.enabled)
		estimate.lamination_required = 1
		estimate.save()
		lamination_row = next(row for row in estimate.applied_cost_drivers
			if "lamination" in row.cost_driver.lower())
		self.assertTrue(lamination_row.enabled)
		self.assertGreater(lamination_row.computed_cost, 0)
		estimate.lamination_required = 0
		estimate.save()
		lamination_row = next(row for row in estimate.applied_cost_drivers
			if "lamination" in row.cost_driver.lower())
		self.assertFalse(lamination_row.enabled)
		self.assertEqual(lamination_row.computed_cost, 0)

		# Packing can be entered where the estimator naturally makes the
		# finishing decision. Blank uses the carton calculation; an entered
		# amount (including zero) drives the row's native override.
		packing_row = next(row for row in estimate.applied_cost_drivers
			if "packing" in row.cost_driver.lower())
		estimate.packing_cost_override_enabled = 1
		estimate.packing_cost = 123
		estimate.save()
		self.assertTrue(packing_row.cost_override_enabled)
		self.assertEqual(packing_row.computed_cost, 123)
		self.assertEqual(packing_row.source, "Manual Override")
		estimate.packing_cost = 0
		estimate.save()
		self.assertEqual(packing_row.computed_cost, 0)
		estimate.packing_cost_override_enabled = 0
		estimate.packing_cost = None
		estimate.save()
		self.assertFalse(packing_row.cost_override_enabled)
		self.assertEqual(packing_row.source, "Calculated")

		# Every cost row's native override must replace the calculated value,
		# including a deliberate override of exactly zero.
		artwork_row = next(row for row in estimate.applied_cost_drivers
			if "artwork" in row.cost_driver.lower())
		original_artwork_cost = artwork_row.computed_cost
		artwork_row.cost_override_enabled = 1
		artwork_row.cost_override = 0
		artwork_row.override_reason = "Regression test: deliberate zero"
		estimate.save()
		self.assertEqual(artwork_row.computed_cost, 0)
		artwork_row.cost_override = original_artwork_cost + 100
		artwork_row.override_reason = "Regression test: confirmed custom amount"
		estimate.save()
		self.assertAlmostEqual(artwork_row.computed_cost, original_artwork_cost + 100, places=2)
		artwork_row.cost_override_enabled = 0
		artwork_row.cost_override = 0
		artwork_row.override_reason = None
		estimate.save()
		self.assertAlmostEqual(artwork_row.computed_cost, original_artwork_cost, places=2)

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
