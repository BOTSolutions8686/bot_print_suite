"""Regression tests for authorization gates around whitelisted APIs."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from bot_print_suite.bot_print_suite.doctype.print_enquiry.print_enquiry import (
	_require_permission as require_enquiry_permission,
)
from bot_print_suite.estimation.quotation_mapper import (
	_require_permission as require_quotation_permission,
)
from bot_print_suite.production.job_tracker import _require_sales_order_read
from bot_print_suite.production.start_production import (
	_require_permission as require_production_permission,
)
from bot_print_suite.utils import assign_job_item_to_quotation


class TestWhitelistedAPIPermissions(unittest.TestCase):
	@patch("frappe.has_permission", return_value=False)
	def test_enquiry_conversion_rejects_missing_destination_permission(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			require_enquiry_permission("Print Estimate", "create")

	@patch("frappe.has_permission", return_value=False)
	def test_quotation_creation_rejects_missing_destination_permission(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			require_quotation_permission("Quotation", "create")

	@patch("frappe.has_permission", return_value=False)
	def test_production_start_rejects_missing_destination_permission(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			require_production_permission("Work Order", "submit")

	@patch("frappe.has_permission", return_value=False)
	def test_job_metrics_require_sales_order_read_permission(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			_require_sales_order_read()


class TestQuotationJobItemAssignment(unittest.TestCase):
	@patch("bot_print_suite.utils.frappe.db.get_value", return_value="Folding Carton - QTN-0001")
	@patch("bot_print_suite.utils._get_or_create_quotation_job_item", return_value="JOB-QTN-0001")
	@patch("bot_print_suite.utils.frappe.get_doc")
	def test_placeholder_is_replaced_before_quotation_submission(
		self, get_doc, _get_job_item, _get_item_name
	):
		get_doc.return_value = SimpleNamespace(product_type="Folding Carton")
		placeholder = SimpleNamespace(
			item_code="PRINT-JOB-FOLDING-CARTON", item_name="Print Job - Folding Carton"
		)
		unrelated = SimpleNamespace(item_code="DELIVERY", item_name="Delivery")
		quotation = SimpleNamespace(
			name="QTN-0001",
			custom_print_estimate="PE-0001",
			items=[placeholder, unrelated],
			get=lambda field: getattr(quotation, field, None),
		)

		assign_job_item_to_quotation(quotation)

		self.assertEqual(placeholder.item_code, "JOB-QTN-0001")
		self.assertEqual(placeholder.item_name, "Folding Carton - QTN-0001")
		self.assertEqual(unrelated.item_code, "DELIVERY")

	@patch("bot_print_suite.utils._get_or_create_quotation_job_item")
	def test_non_print_quotation_is_untouched(self, get_job_item):
		quotation = SimpleNamespace(
			custom_print_estimate=None,
			get=lambda field: getattr(quotation, field, None),
		)

		assign_job_item_to_quotation(quotation)

		get_job_item.assert_not_called()
