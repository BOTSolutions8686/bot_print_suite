import frappe
from frappe.model.document import Document


class PaperType(Document):
	def validate(self):
		self.sheets_per_tonne = (self.reems_per_tonne or 0) * (self.sheets_per_reem or 0)
		if self.sheets_per_tonne:
			self.cost_per_sheet = round((self.rate_per_tonne or 0) / self.sheets_per_tonne, 4)
