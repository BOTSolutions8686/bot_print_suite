import frappe

# (English source string exactly as it appears, Arabic translation)
TRANSLATIONS = [
	# Print Estimate - main fields
	("Customer", "العميل"),
	("Product Estimation Template", "قالب التسعير"),
	("Finished Width (cm)", "العرض النهائي (سم)"),
	("Finished Height (cm)", "الارتفاع النهائي (سم)"),
	("Quantity", "الكمية"),
	("Print Enquiry", "استفسار طباعة"),
	("Margin %", "نسبة الربح %"),
	("Colours", "الألوان"),
	("Colours Front", "الألوان - وجه"),
	("Colours Back", "الألوان - ظهر"),
	("Paper Type", "نوع الورق"),
	("Sheet Size", "مقاس الفرخ"),
	("Press", "المطبعة"),
	("Cost Items", "بنود التكلفة"),
	("Die/Frame Width (cm)", "عرض القالب (سم)"),
	("Die/Frame Height (cm)", "ارتفاع القالب (سم)"),
	("Glue - Number of Sides", "الغراء - عدد الأوجه"),
	("Reusing an existing die for this customer?", "إعادة استخدام قالب موجود لهذا العميل؟"),
	("Freight Cost", "تكلفة الشحن"),
	("Additional Quantity Breaks", "كميات إضافية"),
	("Additional Quantities to Quote", "كميات إضافية للتسعير"),
	("Sell Price", "سعر البيع"),
	("Ups per Sheet", "عدد القطع في الفرخ"),
	("Sheets Required", "الأفرخ المطلوبة"),
	("Cost Items Total", "إجمالي بنود التكلفة"),
	("How is this calculated?", "كيف يتم حساب هذا؟"),
	("Cost Breakdown (Sales Manager Only)", "تفصيل التكلفة (لمدير المبيعات فقط)"),
	("Paper Cost", "تكلفة الورق"),
	("Subtotal (Total Cost)", "المجموع (التكلفة الإجمالية)"),
	("Quantity Break Results", "نتائج الكميات الإضافية"),

	# Print Estimate Cost Driver Line (child table)
	("Cost Driver", "بند التكلفة"),
	("Enabled", "مفعّل"),
	("Basis", "الأساس"),
	("Computed Cost", "التكلفة المحسوبة"),

	# Print Estimate Qty Break / Break Result (child tables)
	("Qty", "الكمية"),

	# Product Estimation Template
	("Template Name", "اسم القالب"),
	("Product Type", "نوع المنتج"),
	("Notes", "ملاحظات"),
	("Required", "إلزامي"),
	("On by Default", "مفعّل افتراضياً"),

	# Cost Driver master
	("Driver Name", "اسم البند"),
	("Measurement Basis", "أساس القياس"),
	("Fixed Setup Cost", "تكلفة تجهيز ثابتة"),
	("Rate Varies by Quantity (Tiered)", "السعر يتغير حسب الكمية (متدرج)"),
	("Rate (if not tiered)", "السعر (إن لم يكن متدرجاً)"),
	("Tiers", "المستويات"),
	("From Qty", "من كمية"),
	("To Qty", "إلى كمية"),
	("Rate", "السعر"),

	# Paper Type master
	("Rate per Tonne", "السعر لكل طن"),
	("Reems per Tonne", "عدد الرزم لكل طن"),
	("Sheets per Reem", "عدد الأفرخ لكل رزمة"),
	("Sheets per Tonne (computed)", "الأفرخ لكل طن (محسوب)"),
	("Cost per Sheet (computed)", "تكلفة الفرخ (محسوبة)"),

	# Select field options used on Print Estimate / Cost Driver
	("Per cm2", "لكل سم²"),
	("Per 1000 Sheets", "لكل 1000 فرخ"),
	("Per 1000 Pieces", "لكل 1000 قطعة"),
	("Per Sheet", "لكل فرخ"),
	("Per Side", "لكل وجه"),
	("Per Colour", "لكل لون"),
	("Flat Fee", "رسم ثابت"),
	("Per Hour", "لكل ساعة"),
	("Folding Carton", "كرتون مطوي"),
	("Commercial", "تجاري"),
	("Label", "ملصق"),
]


def run():
	created, updated = 0, 0
	for source, target in TRANSLATIONS:
		existing = frappe.db.exists("Translation", {"source_text": source, "language": "ar"})
		if existing:
			doc = frappe.get_doc("Translation", existing)
			if doc.translated_text != target:
				doc.translated_text = target
				doc.save(ignore_permissions=True)
				updated += 1
		else:
			frappe.get_doc({
				"doctype": "Translation",
				"language": "ar",
				"source_text": source,
				"translated_text": target,
			}).insert(ignore_permissions=True)
			created += 1
	frappe.db.commit()
	print(f"Created: {created}, Updated: {updated}, Total: {len(TRANSLATIONS)}")
