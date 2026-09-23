import frappe
from frappe.model.document import Document


class PrintEnquiry(Document):
	def before_insert(self):
		# Public web enquiries should never have to know the internal source
		# field exists. Desk users can still choose another channel.
		if not self.source:
			self.source = "Portal"

	@frappe.whitelist()
	def make_print_estimate(self):
		"""Creates a linked Print Estimate pre-filled from whatever
		structured fields were captured on this enquiry, and moves the
		enquiry to 'Estimating'. Customer/spec fields not captured here
		are left for the estimator to fill on the estimate itself -
		this is a starting point, not a full auto-fill."""
		self.check_permission("write")
		_require_permission("Print Estimate", "create")
		if self.linked_estimate:
			frappe.throw("An estimate is already linked to this enquiry.")
		if not self.customer:
			self.customer = self._get_or_create_customer()

		template = {
			"Folding Carton": "Folding Carton",
			"Business Card": "Business Card",
			"Flyer": "Flyer",
		}.get(self.product_type)

		estimate = frappe.get_doc({
			"doctype": "Print Estimate",
			"customer": self.customer,
			"enquiry": self.name,
			"product_template": template,
			"product_type": "Commercial" if self.product_type == "Business Card" else self.product_type,
			"finished_width_cm": self.finished_width_cm or 0,
			"finished_height_cm": self.finished_height_cm or 0,
			"quantity": self.requested_quantity or 0,
			"colours_front": self.colours_front or 0,
			"colours_back": self.colours_back or 0,
			"double_sided": 1 if self.printing_sides == "Both sides" else 0,
			"printing_method": "Sheetwise",
			"ink_coverage": "Medium",
		})
		estimate.insert(ignore_permissions=True, ignore_mandatory=True)

		self.linked_estimate = estimate.name
		self.status = "Estimating"
		self.save(ignore_permissions=True)

		return estimate.name

	def _get_or_create_customer(self):
		"""Turn a customer-facing company name into a proper ERPNext Customer
		at the deliberate internal conversion step, never during anonymous
		web submission. Reuse an exact existing name where possible."""
		name = (self.customer_name_new or "").strip()
		if not name:
			frappe.throw("Link an existing Customer or enter the new company name before converting.")

		existing = frappe.db.get_value("Customer", {"customer_name": name}, "name")
		if existing:
			return existing
		_require_permission("Customer", "create")

		customer_group = frappe.db.get_single_value("Selling Settings", "customer_group")
		if not customer_group or frappe.db.get_value("Customer Group", customer_group, "is_group"):
			customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
		if not customer_group:
			frappe.throw("No usable Customer Group exists. Create a non-group Customer Group before converting this enquiry.")
		territory = frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"
		customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": name,
			"customer_type": "Company",
			"customer_group": customer_group,
			"territory": territory,
		}).insert(ignore_permissions=True)
		return customer.name


def _require_permission(doctype, permission_type):
	if not frappe.has_permission(doctype, ptype=permission_type):
		frappe.throw(
			f"You need {permission_type} permission on {doctype} to convert this enquiry.",
			frappe.PermissionError,
		)
