import frappe


def run():
	ws = frappe.get_doc("Workspace", "Print Suite")
	print("TITLE:", ws.title, "MODULE:", ws.module, "PUBLIC:", ws.public)
	print("NUMBER_CARDS:", [c.number_card_name for c in ws.number_cards])
	print("CHARTS:", [c.chart_name for c in ws.charts])
	print("SHORTCUTS:", [(s.label, s.link_to) for s in ws.shortcuts])
	import json
	blocks = json.loads(ws.content)
	print("CONTENT_BLOCKS:", len(blocks), "types:", [b["type"] for b in blocks])
