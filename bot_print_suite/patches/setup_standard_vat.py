import frappe

from bot_print_suite.setup.vat import ensure_standard_vat_template


def execute():
	template_name = ensure_standard_vat_template()
	if not template_name:
		return

	# Quotations created before this migration should receive the same VAT
	# while they are still drafts. Submitted or unrelated quotations remain
	# untouched.
	for row in frappe.get_all(
		"Quotation",
		filters={
			"docstatus": 0,
			"custom_print_estimate": ["is", "set"],
		},
		fields=["name", "custom_print_estimate", "taxes_and_charges"],
	):
		if not frappe.db.exists("Print Estimate", row.custom_print_estimate):
			continue
		quotation = frappe.get_doc("Quotation", row.name)
		if quotation.taxes:
			continue
		if row.taxes_and_charges and row.taxes_and_charges != template_name:
			continue
		quotation.taxes_and_charges = template_name
		quotation.set("taxes", [])
		quotation.append_taxes_from_master()
		quotation.save(ignore_permissions=True)
