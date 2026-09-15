import frappe
from frappe.model.document import Document


class JobArtwork(Document):
	def on_update(self):
		# Revision Requested -> spawn the next version automatically as a
		# fresh Draft, so the "each revision is its own record" versioning
		# from PLAN.md section 4 happens without the estimator having to
		# remember to do it manually. Guarded by existence check rather than
		# a flag field, so no schema change is needed for this.
		if self.status != "Revision Requested":
			return
		next_version_no = (self.version_no or 1) + 1
		exists = frappe.db.exists("Job Artwork", {
			"sales_order": self.sales_order, "version_no": next_version_no,
		})
		if not exists:
			frappe.get_doc({
				"doctype": "Job Artwork",
				"sales_order": self.sales_order,
				"version_no": next_version_no,
				"status": "Draft",
			}).insert(ignore_permissions=True)
