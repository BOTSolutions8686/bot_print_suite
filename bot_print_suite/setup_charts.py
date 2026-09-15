import frappe


def _make_chart(name, chart_name, doctype, chart_type, based_on, value_field=None, group_by_type=None):
	if frappe.db.exists("Dashboard Chart", name):
		return
	doc = frappe.get_doc({
		"doctype": "Dashboard Chart",
		"name": name,
		"chart_name": chart_name,
		"chart_type": chart_type,  # "Count" or "Group By" or "Sum"
		"document_type": doctype,
		"based_on": based_on,
		"timespan": "Last Year",
		"time_interval": "Monthly",
		"type": "Bar",
		"filters_json": "[]",
		"is_public": 1,
		"currency": None,
	})
	if group_by_type:
		doc.group_by_type = group_by_type
		doc.group_by_based_on = value_field
	frappe.get_doc(doc.as_dict()).insert(ignore_permissions=True)


def run():
	_make_chart("Monthly Sales", "Monthly Sales", "Sales Order", "Count", "transaction_date")

	_make_chart("Enquiry Source Breakdown", "Enquiry Source Breakdown", "Print Enquiry",
		"Group By", "creation", value_field="source", group_by_type="Count")

	frappe.db.commit()
	print("CHARTS_CREATED")
