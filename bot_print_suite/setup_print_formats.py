import frappe

JOB_TICKET_HTML = """
<div style="font-family: Arial, sans-serif; padding: 10px;">
  <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:3px solid #1B2A4A; padding-bottom:10px; margin-bottom:16px;">
    <div>
      <div style="font-size:11px; color:#666;">JOB TICKET / بطاقة العمل</div>
      <div style="font-size:26px; font-weight:bold; letter-spacing:1px; font-family: 'Courier New', monospace;">{{ doc.name }}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px; color:#666;">Status / الحالة</div>
      <div style="font-size:16px; font-weight:bold;">{{ doc.custom_job_status or "Prepress" }}</div>
    </div>
  </div>

  <table style="width:100%; border-collapse:collapse; margin-bottom:14px;">
    <tr>
      <td style="width:50%; padding:4px 0; vertical-align:top;">
        <div style="font-size:11px; color:#666;">Customer / العميل</div>
        <div style="font-size:14px; font-weight:bold;">{{ doc.customer_name or doc.customer }}</div>
      </td>
      <td style="width:50%; padding:4px 0; vertical-align:top;">
        <div style="font-size:11px; color:#666;">Customer PO / رقم أمر الشراء</div>
        <div style="font-size:14px; font-weight:bold;">{{ doc.po_no or "-" }}</div>
      </td>
    </tr>
    <tr>
      <td style="padding:4px 0; vertical-align:top;">
        <div style="font-size:11px; color:#666;">Delivery Date / تاريخ التسليم</div>
        <div style="font-size:14px; font-weight:bold;">{{ frappe.utils.formatdate(doc.delivery_date) if doc.delivery_date else "-" }}</div>
      </td>
      <td style="padding:4px 0; vertical-align:top;">
        <div style="font-size:11px; color:#666;">Order Date / تاريخ الطلب</div>
        <div style="font-size:14px; font-weight:bold;">{{ frappe.utils.formatdate(doc.transaction_date) }}</div>
      </td>
    </tr>
  </table>

  <div style="font-size:12px; font-weight:bold; color:#1B2A4A; border-bottom:1px solid #ccc; margin-bottom:6px;">
    Job Specification / مواصفات العمل
  </div>
  <table style="width:100%; border-collapse:collapse; font-size:12px;">
    <thead>
      <tr style="background:#f2f4f8;">
        <th style="text-align:left; padding:6px; border:1px solid #ddd;">Item / الصنف</th>
        <th style="text-align:right; padding:6px; border:1px solid #ddd;">Qty / الكمية</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr>
        <td style="padding:6px; border:1px solid #ddd;">{{ row.item_name or row.item_code }}</td>
        <td style="text-align:right; padding:6px; border:1px solid #ddd;">{{ "{:,.0f}".format(row.qty) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div style="margin-top:20px; padding:10px; border:1px dashed #999; font-size:11px; color:#666;">
    Routing: Prepress &rarr; CTP &rarr; Press &rarr; Finishing &rarr; QC &rarr; Delivery
    <br>Operator sign-off / توقيع المشغل: ______________________
  </div>
</div>
"""

QUOTATION_HTML = """
<div style="font-family: Arial, sans-serif; padding: 10px;">
  <div style="display:flex; justify-content:space-between; border-bottom:3px solid #1B2A4A; padding-bottom:12px; margin-bottom:16px;">
    <div>
      <div style="font-size:20px; font-weight:bold; color:#1B2A4A;">BOT Solutions</div>
      <div style="font-size:11px; color:#666;">Print Estimation & Job Management</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px; color:#666;">Quotation / عرض السعر</div>
      <div style="font-size:16px; font-weight:bold;">{{ doc.name }}</div>
      <div style="font-size:11px; color:#666;">{{ frappe.utils.formatdate(doc.transaction_date) }}</div>
    </div>
  </div>

  <div style="margin-bottom:14px;">
    <div style="font-size:11px; color:#666;">To / إلى</div>
    <div style="font-size:14px; font-weight:bold;">{{ doc.customer_name or doc.party_name }}</div>
  </div>

  <table style="width:100%; border-collapse:collapse; font-size:12px; margin-bottom:16px;">
    <thead>
      <tr style="background:#1B2A4A; color:#fff;">
        <th style="text-align:left; padding:8px;">Description / الوصف</th>
        <th style="text-align:right; padding:8px;">Qty / الكمية</th>
        <th style="text-align:right; padding:8px;">Rate / السعر</th>
        <th style="text-align:right; padding:8px;">Amount / المبلغ</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr style="border-bottom:1px solid #eee;">
        <td style="padding:8px;">{{ row.item_name or row.item_code }}</td>
        <td style="text-align:right; padding:8px;">{{ "{:,.0f}".format(row.qty) }}</td>
        <td style="text-align:right; padding:8px;">{{ frappe.utils.fmt_money(row.rate, currency=doc.currency) }}</td>
        <td style="text-align:right; padding:8px;">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div style="display:flex; justify-content:flex-end;">
    <table style="width:280px; font-size:13px;">
      <tr>
        <td style="padding:4px 8px; text-align:right;">Grand Total / الإجمالي</td>
        <td style="padding:4px 8px; text-align:right; font-weight:bold; font-size:16px;">{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</td>
      </tr>
    </table>
  </div>

  <div style="margin-top:24px; font-size:10px; color:#999; border-top:1px solid #eee; padding-top:8px;">
    This quotation is subject to BOT Solutions' standard terms. Prices exclude VAT unless stated.
    <br>هذا العرض خاضع للشروط والأحكام القياسية لشركة BOT Solutions. الأسعار غير شاملة ضريبة القيمة المضافة ما لم يذكر خلاف ذلك.
  </div>
</div>
"""


def run():
	if not frappe.db.exists("Print Format", "Job Ticket"):
		frappe.get_doc({
			"doctype": "Print Format",
			"name": "Job Ticket",
			"doc_type": "Sales Order",
			"module": "BOT Print Suite",
			"print_format_type": "Jinja",
			"standard": "Yes",
			"disabled": 0,
			"html": JOB_TICKET_HTML,
		}).insert(ignore_permissions=True)
		print("JOB_TICKET_CREATED")
	else:
		print("JOB_TICKET_EXISTS")


	if not frappe.db.exists("Print Format", "Print Quotation"):
		frappe.get_doc({
			"doctype": "Print Format",
			"name": "Print Quotation",
			"doc_type": "Quotation",
			"module": "BOT Print Suite",
			"print_format_type": "Jinja",
			"standard": "Yes",
			"disabled": 0,
			"html": QUOTATION_HTML,
		}).insert(ignore_permissions=True)
		print("QUOTATION_FORMAT_CREATED")
	else:
		print("QUOTATION_FORMAT_EXISTS")

	frappe.db.commit()
