import frappe


VAT_RATE = 15
VAT_TEMPLATE_TITLE = "Standard VAT 15%"


def ensure_standard_vat_template(company=None):
	"""Return a real ERPNext Sales Taxes template for Saudi 15% VAT."""
	company = company or frappe.defaults.get_global_default("company")
	if not company:
		return None

	existing = frappe.db.get_value(
		"Sales Taxes and Charges Template",
		{"company": company, "title": VAT_TEMPLATE_TITLE, "disabled": 0},
		"name",
	)
	if existing:
		if not frappe.db.get_value("Sales Taxes and Charges Template", existing, "is_default"):
			frappe.db.set_value("Sales Taxes and Charges Template", existing, "is_default", 1)
		return existing

	abbr = frappe.db.get_value("Company", company, "abbr")
	parent = frappe.db.get_value(
		"Account",
		{"company": company, "account_name": "Duties and Taxes", "is_group": 1},
		"name",
	)
	if not parent:
		frappe.throw(f"Duties and Taxes account group is missing for {company}.")

	account_name = f"VAT Output 15% - {abbr}"
	if not frappe.db.exists("Account", account_name):
		frappe.get_doc({
			"doctype": "Account",
			"account_name": "VAT Output 15%",
			"parent_account": parent,
			"company": company,
			"account_type": "Tax",
			"root_type": "Liability",
			"is_group": 0,
		}).insert(ignore_permissions=True)

	template = frappe.get_doc({
		"doctype": "Sales Taxes and Charges Template",
		"title": VAT_TEMPLATE_TITLE,
		"company": company,
		"is_default": 1,
		"taxes": [{
			"charge_type": "On Net Total",
			"account_head": account_name,
			"description": "VAT 15% / ضريبة القيمة المضافة ١٥٪",
			"rate": VAT_RATE,
		}],
	}).insert(ignore_permissions=True)
	return template.name
