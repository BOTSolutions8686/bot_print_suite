import frappe

# Full field-description translations for Print Estimate - the actual
# help text users see, not just labels. Source strings must match the
# doctype JSON's "description" property EXACTLY (Frappe's translation
# lookup is a literal string match).
DESCRIPTIONS = [
	("The client this job is for. Must already exist as a Customer, or be created first.",
	 "العميل الذي من أجله هذه الشغلة. يجب أن يكون موجوداً كعميل مسبقاً، أو يتم إنشاؤه أولاً."),
	("Pick a template (Folding Carton, Business Card, Sticker...) to pull in the right cost items automatically - like choosing a BOM. You can still add or remove individual items for this one job afterward without touching the template itself.",
	 "اختر قالباً (كرتون مطوي، كرت شخصي، ستيكر...) لسحب بنود التكلفة الصحيحة تلقائياً - مثل اختيار قائمة مواد. يمكنك إضافة أو حذف بنود فردية لهذه الشغلة فقط دون التأثير على القالب نفسه."),
	("The flat, printed piece's own size, in centimetres - matching how you'd naturally give it (e.g. 51). Not the sheet size, and not the closed/folded size for a box - the flat blank as it sits on the press sheet.",
	 "مقاس القطعة المطبوعة وهي مفرودة، بالسنتيمتر - بنفس الطريقة التي تعطيها بها عادة (مثال: 51). ليس مقاس الفرخ، وليس مقاس الكرتون بعد الطي - المقاس وهو مفروش على فرخ الطباعة."),
	("See Finished Width - same effect, the other dimension.",
	 "نفس فكرة العرض النهائي - البعد الآخر."),
	("How many finished pieces the customer wants. Drives Sheets Required, and therefore every quantity-based Cost Item. To quote several quantities at once, add extra rows under \"Additional Quantities to Quote\" below instead of changing this field repeatedly.",
	 "كم قطعة نهائية يريدها العميل. يحدد عدد الأفرخ المطلوبة، وبالتالي كل بند تكلفة يعتمد على الكمية. لتسعير عدة كميات دفعة واحدة، أضف صفوفاً إضافية تحت \"كميات إضافية للتسعير\" بدلاً من تغيير هذا الحقل مراراً."),
	("Auto-filled when this estimate was created from an enquiry via \"Convert to Estimate\". Leave blank for an estimate started directly.",
	 "يُملأ تلقائياً عند إنشاء هذا التقدير من استفسار عبر \"تحويل إلى تقدير\". اتركه فارغاً إذا بدأت التقدير مباشرة."),
	("The only field that changes Sell Price without changing the underlying cost.",
	 "الحقل الوحيد الذي يغيّر سعر البيع دون تغيير التكلفة الأساسية."),
	("Set automatically from the Template picked above - used for reporting only.",
	 "يُحدد تلقائياً من القالب المختار أعلاه - يُستخدم للتقارير فقط."),
	("Number of ink colours printed on the front (e.g. 4 for full-colour CMYK). Drives the Plate Cost Item.",
	 "عدد ألوان الحبر المطبوعة على الوجه (مثال: 4 للألوان الكاملة CMYK). يحدد بند تكلفة البليت."),
	("Number of colours on the back. Leave at 0 for single-sided jobs.",
	 "عدد الألوان على الظهر. اتركه 0 للشغلات وجه واحد فقط."),
	("Pick the real paper stock and weight from the list - the rate is already set up behind this.",
	 "اختر نوع الورق ووزنه الحقيقي من القائمة - السعر معدّ مسبقاً خلف هذا الاختيار."),
	("Which standard stock sheet this job is planned on.",
	 "مقاس الفرخ القياسي الذي ستُطبع عليه هذه الشغلة."),
	("Which machine runs this job.",
	 "الماكينة التي ستشغّل هذه الشغلة."),
	("Populated from the Template above. Uncheck a row to drop it from this job, or add another Cost Driver row - only this estimate is affected, the template itself is unchanged.",
	 "يُملأ من القالب أعلاه. أزل التحديد عن أي صف لإسقاطه من هذه الشغلة، أو أضف بند تكلفة آخر - هذا يؤثر على هذا التقدير فقط، القالب نفسه لا يتغير."),
	("The die's own width, e.g. 53. Only needed if this job's Cost Items include Die/Frame.",
	 "عرض القالب نفسه، مثال: 53. مطلوب فقط إذا كانت بنود هذه الشغلة تشمل القالب/الفريم."),
	("The die's own height, e.g. 45.",
	 "ارتفاع القالب نفسه، مثال: 45."),
	("How many sides get glued (0 if this job doesn't need gluing).",
	 "كم عدد الأوجه التي سيتم لصقها (0 إذا كانت هذه الشغلة لا تحتاج لصقاً)."),
	("Repeat customers don't pay for the die again - check this on a reorder of the same design.",
	 "العملاء المتكررون لا يدفعون تكلفة القالب مرة أخرى - فعّل هذا الخيار عند تكرار نفس التصميم."),
	("Delivery cost to the customer's location, if applicable. Added straight into the total.",
	 "تكلفة توصيل الشغلة لموقع العميل، إن وجدت. تُضاف مباشرة إلى الإجمالي."),
	("Want to offer the customer a price at 5,000 / 10,000 / 20,000 in one quotation? Add one row per extra quantity here.",
	 "تريد تقديم سعر للعميل بكميات 5,000 / 10,000 / 20,000 في عرض سعر واحد؟ أضف صفاً لكل كمية إضافية هنا."),
	("Nothing below this line is entered by hand. If a number here looks wrong, the fix is always in a field above, not here.",
	 "لا شيء تحت هذا الخط يُدخل يدوياً. إذا بدا رقم هنا خاطئاً، فالتصحيح يكون دائماً في حقل أعلاه، وليس هنا."),
	("The final quoted price for this job. This is what becomes the Quotation line.",
	 "السعر النهائي المقدَّم لهذه الشغلة. هذا ما يصبح بند عرض السعر."),
	("How many finished pieces fit on one press sheet.",
	 "كم قطعة نهائية تتسع في فرخ طباعة واحد."),
	("Quantity \u00f7 Ups, plus make-ready and running waste.",
	 "الكمية \u00f7 عدد القطع في الفرخ، بالإضافة لهدر التجهيز وهدر التشغيل."),
	("Sum of all enabled Cost Items above.",
	 "مجموع كل بنود التكلفة المفعّلة أعلاه."),
	("Sheets Required \u00d7 the price per sheet.",
	 "الأفرخ المطلوبة \u00d7 سعر الفرخ."),
	("Paper + Cost Items Total + Freight. This is the true cost - Sell Price is this plus margin.",
	 "الورق + إجمالي بنود التكلفة + الشحن. هذه هي التكلفة الحقيقية - سعر البيع هو هذا بالإضافة إلى الربح."),
]


def run():
	created, updated = 0, 0
	for source, target in DESCRIPTIONS:
		existing = frappe.db.exists("Translation", {"source_text": source, "language": "ar"})
		if existing:
			doc = frappe.get_doc("Translation", existing)
			if doc.translated_text != target:
				doc.translated_text = target
				doc.save(ignore_permissions=True)
				updated += 1
		else:
			frappe.get_doc({
				"doctype": "Translation", "language": "ar",
				"source_text": source, "translated_text": target,
			}).insert(ignore_permissions=True)
			created += 1
	frappe.db.commit()
	print(f"Created: {created}, Updated: {updated}, Total: {len(DESCRIPTIONS)}")
