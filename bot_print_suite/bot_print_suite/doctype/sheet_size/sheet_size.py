import frappe
from frappe.model.document import Document


class SheetSize(Document):
	def validate(self):
		# Mofeed's real sheet sizes are all in cm (e.g. 70x100) - compute
		# the mm values the estimation engine actually needs, so nobody
		# setting up a new Sheet Size record has to do that conversion
		# by hand.
		self.width_mm = round(float(self.width_cm or 0) * 10, 2)
		self.height_mm = round(float(self.height_cm or 0) * 10, 2)
