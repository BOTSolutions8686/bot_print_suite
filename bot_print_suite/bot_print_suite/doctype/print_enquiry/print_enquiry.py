import frappe
from frappe.model.document import Document


class PrintEnquiry(Document):
	@frappe.whitelist()
	def make_print_estimate(self):
		"""Creates a linked Print Estimate pre-filled from whatever
		structured fields were captured on this enquiry, and moves the
		enquiry to 'Estimating'. Customer/spec fields not captured here
		are left for the estimator to fill on the estimate itself -
		this is a starting point, not a full auto-fill."""
		if self.linked_estimate:
			frappe.throw("An estimate is already linked to this enquiry.")
		if not self.customer:
			frappe.throw("Link an existing Customer before converting to an estimate.")

		estimate = frappe.get_doc({
			"doctype": "Print Estimate",
			"customer": self.customer,
			"enquiry": self.name,
			"product_type": self.product_type or "Commercial",
			"finished_size_w": 0,
			"finished_size_h": 0,
			"quantity": 0,
			"colours_front": 0,
			"printing_method": "Sheetwise",
			"ink_coverage": "Medium",
		})
		estimate.insert(ignore_permissions=True, ignore_mandatory=True)

		self.linked_estimate = estimate.name
		self.status = "Estimating"
		self.save(ignore_permissions=True)

		return estimate.name
