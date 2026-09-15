import frappe
from frappe.utils.print_format import download_multi_pdf
from frappe.www.printview import get_html_and_style


def run():
	html1 = get_html_and_style(doc="Sales Order", name="GA-JOB-2026-0001", print_format="Job Ticket")
	print("JOB_TICKET_RENDER_OK, length:", len(html1["html"]))
	print("Contains job number:", "GA-JOB-2026-0001" in html1["html"])
	print("Contains customer:", "Golden Arrow" in html1["html"])

	qtn_name = frappe.db.get_value("Quotation", {"docstatus": 1}, "name")
	html2 = get_html_and_style(doc="Quotation", name=qtn_name, print_format="Print Quotation")
	print("QUOTATION_RENDER_OK, length:", len(html2["html"]))
	print("Contains grand total formatting:", "SAR" in html2["html"] or "ر.س" in html2["html"])
