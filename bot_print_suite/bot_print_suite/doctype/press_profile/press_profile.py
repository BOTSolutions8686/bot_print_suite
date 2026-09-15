import frappe
from frappe.model.document import Document


class PressProfile(Document):
	def validate(self):
		self.max_sheet_width_mm = round(float(self.max_sheet_width_cm or 0) * 10, 2)
		self.max_sheet_height_mm = round(float(self.max_sheet_height_cm or 0) * 10, 2)
