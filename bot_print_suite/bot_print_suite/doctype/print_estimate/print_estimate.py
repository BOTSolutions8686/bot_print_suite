import frappe
from frappe.model.document import Document
from bot_print_suite.estimation.engine import compute_estimate
from bot_print_suite.estimation.quotation_mapper import make_quotation
from bot_print_suite.estimation.cost_driver_binding import (
	apply_template as _apply_template, compute_driver_costs, build_reconciliation_table,
	enforce_template_requirements, sync_glue_configuration)


class PrintEstimate(Document):
	def validate(self):
		# Present the die decision in plain language while retaining the
		# established boolean used by the costing engine. "Not sure" is
		# deliberately conservative and includes the new-die charge.
		if self.die_requirement:
			self.reusing_existing_die = self.die_requirement == "Existing die available"

		# Templates are now mandatory (product_template is reqd=1) - the
		# old static, non-templated calculation path has been removed
		# entirely, not just hidden. Every estimate goes through the
		# same Cost Driver pipeline.

		# Auto-apply the template on the natural first save, if no Cost
		# Items exist yet - matches how a real estimator actually works
		# (pick a template as part of filling in the job, not a separate
		# extra click afterward). Safe specifically because it only
		# fires when the table is empty - an already-populated, hand-
		# edited estimate is never touched by this; re-applying later is
		# what the explicit "Apply Template" button on the form is for.
		if self.product_template and not self.get("applied_cost_drivers"):
			_apply_template(self)

		# The visible glue choice and the enabled Glue cost row must never
		# disagree. The confirmed rate is specifically for one-side gluing,
		# so this is a simple yes/no field rather than a misleading count.
		sync_glue_configuration(self)

		# product_type is now a hidden, reporting-only field, auto-set
		# from the template rather than asked of the user - one less
		# thing to fill in that was never part of the real calculation.
		if self.product_template:
			template_product_type = frappe.db.get_value(
				"Product Estimation Template", self.product_template, "product_type")
			if template_product_type:
				self.product_type = template_product_type

		# A freshly converted-from-enquiry estimate may not yet have its
		# press/sheet_size chosen - skip calculation until the estimator
		# fills in enough to actually compute (avoids crashing on a blank
		# Press Profile / Sheet Size link during that draft stage).
		if self.press and self.sheet_size and self.quantity and self.substrate and self.gsm:
			# Mofeed's real numbers are all in centimetres (51, 45, 53...) -
			# converting to millimetres here means nobody using the form
			# has to do that mental x10 conversion themselves, and the
			# ups-per-sheet geometry engine underneath (which genuinely
			# needs mm, unchanged) never has to know cm exists.
			self.finished_size_w = round(float(self.finished_width_cm or 0) * 10, 2)
			self.finished_size_h = round(float(self.finished_height_cm or 0) * 10, 2)

			# Die area is computed from width x height, not typed in
			# directly - Mofeed's own numbers came as the die's
			# dimensions (53x45cm), not a pre-multiplied area.
			self.die_area_cm2 = round(float(self.die_width_cm or 0) * float(self.die_height_cm or 0), 2)

			compute_estimate(self)
			compute_driver_costs(self)
			enforce_template_requirements(self)

			self.subtotal = round(
				float(self.paper_cost or 0) + float(self.driver_costs_total or 0)
				+ float(self.freight_cost or 0), 2)
			# Explicit float() - a fresh estimate's margin_pct default
			# arrives as the STRING "20", not the number 20, and
			# margin_pct / 100 crashes with a TypeError otherwise. Found
			# via a real Save-button test, not caught by any script test.
			self.sell_price = round(self.subtotal * (1 + float(self.margin_pct or 0) / 100), 2)

			self.reconciliation_table_data = build_reconciliation_table(self)

	@frappe.whitelist()
	def apply_template(self):
		"""Pulls in the selected Product Estimation Template's cost
		items - the 'choose a BOM' moment. Explicit action, not
		automatic on save, so switching templates never silently
		overwrites rows an estimator already hand-edited for this
		specific job without them asking for it."""
		self.check_permission("write")
		_apply_template(self)
		self.save(ignore_permissions=True)
		return len(self.applied_cost_drivers or [])

	@frappe.whitelist()
	def create_quotation(self, qty=None):
		"""Maps this estimate (or one chosen quantity-break row) into a
		draft ERPNext Quotation. Approval happens via the Quotation
		Approval workflow on the Quotation itself, not here."""
		self.check_permission("write")
		quotation = make_quotation(self.name, qty)
		quotation.insert(ignore_permissions=True)
		if self.enquiry:
			frappe.db.set_value("Print Enquiry", self.enquiry, "status", "Quoted")
		return quotation.name
