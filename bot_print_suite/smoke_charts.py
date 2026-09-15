import frappe
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get

def run():
	for name in ["Monthly Sales", "Enquiry Source Breakdown"]:
		try:
			data = get(chart_name=name)
			print(f"{name}: labels={data.get('labels')} datasets={data.get('datasets')}")
		except Exception as e:
			print(f"{name}: ERROR - {e}")
