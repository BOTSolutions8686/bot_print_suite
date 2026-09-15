import frappe

def run():
	frappe.clear_cache()
	print("Cache cleared")
